#!/usr/bin/env python
"""
Read and convert ODS files created by OpenOffice.org's Calc.
"""
import csv
import xml.dom.minidom
import logging
import optparse
import os
import sys
import tools
import xml.sax
import zipfile

class AbstractOdsContentHandler(xml.sax.ContentHandler):
    """
    Sax ContentHandler for content.xml in ODS.
    """
    def __init__(self, sheet=1):
        assert sheet >= 1 

        xml.sax.ContentHandler.__init__(self)
        self.tablesToSkip = sheet
        self._log = logging.getLogger("cutplace.ods")
        
    def startDocument(self):
        self.row = None
        self.cellText = None
        self.indent = 0
        self.insideCell = False
    
    def startElement(self, name, attributes):
        self.indent += 1
        if name == "table:table":
            self.tablesToSkip -= 1
            self._log.debug("%s<%s> #%d" % (" " * 2 * self.indent, name, self.tablesToSkip))
        elif (name == "table:table-cell") and (self.tablesToSkip == 0):
            try:
                self.numberColumnsRepeated = long(attributes.getValue("table:number-columns-repeated"))
            except KeyError:
                self.numberColumnsRepeated = 1
            self._log.debug("%s<%s> (%d) %r" % (" " * 2 * self.indent, name, self.numberColumnsRepeated, attributes.items()))
            self.insideCell = True
            self.cellText = ""
        elif (name == "table:table-row") and (self.tablesToSkip == 0):
            self._log.debug("%s<%s>" % (" " * 2 * self.indent, name))
            self.row = []

    def characters(self, text):
        if self.insideCell and (self.tablesToSkip == 0):
            self._log.debug("%s%r" % (" " * 2 * (self.indent + 1), text))
            self.cellText += text

    def endElement(self, name):
        self.indent -= 1
        if (name == "table:table-cell") and (self.tablesToSkip == 0):
            assert self.cellText is not None
            self.insideCell = False
            for i in range(0, self.numberColumnsRepeated):
                self.row.append(self.cellText)
            self.cellText = None
        if (name == "table:table-row") and (self.tablesToSkip == 0):
            assert self.row is not None
            self.rowCompleted()
            self.row = None
            
    def rowCompleted(self):
        """
        Actions to be performed once `self.row` is complete and can be processed.
        """
        raise NotImplementedError("rowCompleted must be implemented")
        
class OdsToCsvContentHandler(AbstractOdsContentHandler):
    def __init__(self, csvWriter, sheet=1):
        assert csvWriter is not None
        assert sheet >= 1

        AbstractOdsContentHandler.__init__(self, sheet)
        self.csvWriter = csvWriter

    def rowCompleted(self):
        self.csvWriter.writerow(self.row)

class RowListContentHandler(AbstractOdsContentHandler):
    """
    ContentHandler to collect all rows in a list which can be accessed using the `rows` attribute.
    """
    def __init__(self, sheet=1):
        AbstractOdsContentHandler.__init__(self, sheet)
        self.rows = []

    def rowCompleted(self):
        self.rows.append(self.row)

def toCsv(odsFilePath, csvTargetPath, dialect="excel", sheet=1):
    """
    Convert ODS file in `odsFilePath` to CSV using `dialect` and store the result in `csvTargetPath`.
    """
    assert odsFilePath is not None
    assert csvTargetPath is not None
    assert dialect is not None
    assert sheet >= 1
    
    zipArchive = zipfile.ZipFile(odsFilePath, "r")
    try:
        # TODO: Consider switching to 2.6 and use ZipFile.open(). This would need less memory.
        xmlData = zipArchive.read("content.xml")
    finally:
        zipArchive.close()

    csvTargetFile = open(csvTargetPath, "w")
    try:
        csvWriter = csv.writer(csvTargetFile, dialect)
        xml.sax.parseString(xmlData, OdsToCsvContentHandler(csvWriter, sheet))
    finally:
        csvTargetFile.close()
 
def _isEmptyRow(row):
    """
    True if row has no items or all items in row are "".
    """
    result = True
    itemIndex = 0
    while result and (itemIndex < len(row)):
        if row[itemIndex] != "":
            result = False
        else:
            itemIndex += 1
    return result
         
def toDocBookXml(odsFilePath, xmlTargetPath, id, title, sheet=1):
    """
    Convert ODS file in `odsFilePath` to DocBook XML and store the result in `xmlTargetPath`.
    """
    assert odsFilePath is not None
    assert xmlTargetPath is not None
    assert id is not None
    assert title is not None

    # Convert ODS to row list.
    zipArchive = zipfile.ZipFile(odsFilePath, "r")
    try:
        # TODO: Consider switching to 2.6 and use ZipFile.open(). This would need less memory.
        xmlData = zipArchive.read("content.xml")
    finally:
        zipArchive.close()
    handler = RowListContentHandler(sheet)
    xml.sax.parseString(xmlData, handler)
    
    # Remove trailing empty rows.
    rows = handler.rows
    rowCount = len(rows)
    while (rowCount > 0) and (_isEmptyRow(rows[rowCount - 1])):
        rowCount -= 1
        del rows[rowCount]

    # Find out the maximum number of columns per row.
    maxColumnCount = 0
    for row in rows:
        columnCount = len(row)
        if columnCount > maxColumnCount:
            maxColumnCount = columnCount

    # Create DOM.
    dom = xml.dom.minidom.Document()
    docType = xml.dom.minidom.getDOMImplementation().createDocumentType("table", "-//OASIS//DTD DocBook XML V4.5//EN", "http://www.oasis-open.org/docbook/xml/4.5/docbookx.dtd")
    dom.appendChild(docType)
    table = dom.createElement("table")
    # TODO: Validate that `id` is valid.
    table.setAttribute("id", id)
    dom.appendChild(table)
    titleElement = dom.createElement("title")
    # TODO: Add option to specify table title.
    titleText = dom.createTextNode(title)
    titleElement.appendChild(titleText)
    table.appendChild(titleElement)
    tgroupElement = dom.createElement("tgroup")
    tgroupElement.setAttribute("cols", str(maxColumnCount))
    table.appendChild(tgroupElement)
    tbody = dom.createElement("tbody")
    tgroupElement.appendChild(tbody)
    for row in rows:
        rowElement = dom.createElement("row")
        tbody.appendChild(rowElement)
        for entry in row:
            entryElement = dom.createElement("entry")
            entryText = dom.createTextNode(entry)
            entryElement.appendChild(entryText)
            rowElement.appendChild(entryElement)

    # Write target file.
    xmlTargetFile = open(xmlTargetPath, "w")
    try:
        xmlTargetFile.write(dom.toprettyxml("  ", encoding="utf-8"))
    finally:
        xmlTargetFile.close()

def main(arguments):
    assert arguments is not None

    _FORMAT_CSV = "csv"
    _FORMAT_DOCBOOK = "docbook"
    _FORMATS = [_FORMAT_CSV, _FORMAT_DOCBOOK]

    usage = "usage: %prog [options] ODS-FILE OUTPUT-FILE"
    parser = optparse.OptionParser(usage)
    parser.set_defaults(format=_FORMAT_CSV, id="insert-id", sheet=1, title="Insert Title")
    parser.add_option("-f", "--format", metavar="FORMAT", type="choice", choices=_FORMATS, dest="format",
                      help="output format: %s (default: %%default)" % tools.humanReadableList(_FORMATS))
    parser.add_option("-i", "--id", metavar="ID", dest="id", help="XML ID table can be referenced with (default: %default)")
    parser.add_option("-s", "--sheet", metavar="SHEET", type="long", dest="sheet", help="sheet to convert (default: %default)")
    parser.add_option("-t", "--title", metavar="TITLE", dest="title", help="title to be used for XML table (default: %default)")
    options, others = parser.parse_args(arguments)

    # TODO: If no output file is specified, derive name from input file.
    if options.sheet < 1:
        logging.getLogger("cutplace.ods").error("option --sheet is %d but must be at least 1" % options.sheet)
        sys.exit(1)
    elif len(others) == 2:
        sourceFilePath = others[0]
        targetFilePath = others[1]
        logging.getLogger("cutplace.ods").info("convert %r to %r using format %r" % (sourceFilePath, targetFilePath, options.format))
        try:
            if options.format == _FORMAT_CSV:
                toCsv(sourceFilePath, targetFilePath, sheet=options.sheet)
            elif options.format == _FORMAT_DOCBOOK:
                toDocBookXml(sourceFilePath, targetFilePath, id=options.id, title=options.title, sheet=options.sheet)
            else: # pragma: no cover
                raise NotImplementedError("format=%r" % (options.format))
        except IOError, error:
            logging.getLogger("cutplace.ods").error("cannot convert ods to csv: %s" % str(error))
            sys.exit(1)
        except Exception, error:
            logging.getLogger("cutplace.ods").error("cannot convert ods to csv: %s" % str(error), exc_info=1)
            sys.exit(1)
    else:
        sys.stderr.write("%s%s" % ("ODS-FILE and OUTPUT-FILE must be specified", os.linesep))
        sys.exit(1)

if __name__ == '__main__': # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace.ods").setLevel(logging.INFO)
    main(sys.argv[1:])
