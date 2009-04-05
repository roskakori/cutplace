#!/usr/bin/env python
import csv
import logging
import os
import sys
import xml.sax
import zipfile

class AbstractOdsContentHandler(xml.sax.ContentHandler):
    """Sax ContentHandler for content.xml in ODS."""
    # FIXME: Read only first table.
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self._log = logging.getLogger("cutplace.ods")
        
    def startDocument(self):
        self.row = None
        self.cellText = None
        self.indent = 0
        self.insideCell = False
    
    def startElement(self, name, attributes):
        self.indent += 1
        if name == "table:table-cell":
            try:
                self.numberColumnsRepeated = long(attributes.getValue("table:number-columns-repeated"))
            except KeyError:
                self.numberColumnsRepeated = 1
            self._log.debug("%s<%s> (%d) %r" % (" " * 2 * self.indent, name, self.numberColumnsRepeated, attributes.items()))
            self.insideCell = True
            self.cellText = ""
        elif name == "table:table-row":
            self._log.debug("%s<%s>" % (" " * 2 * self.indent, name))
            self.row = []

    def characters(self, text):
        if self.insideCell:
            self._log.debug("%s%r" % (" " * 2 * (self.indent + 1), text))
            self.cellText += text

    def endElement(self, name):
        self.indent -= 1
        if name == "table:table-cell":
            assert self.cellText is not None
            self.insideCell = False
            for i in range(0, self.numberColumnsRepeated):
                self.row.append(self.cellText)
            self.cellText = None
        if name == "table:table-row":
            assert self.row is not None
            self.rowCompleted()
            self.row = None
            
    def rowCompleted(self):
        """
        Actions to be performed once `self.row` is complete and can be processed.
        """
        raise NotImplementedError("rowCompleted must be implemented")
        
class OdsToCsvContentHandler(AbstractOdsContentHandler):
    def __init__(self, csvWriter):
        assert csvWriter is not None

        AbstractOdsContentHandler.__init__(self)
        self.csvWriter = csvWriter

    def rowCompleted(self):
        self.csvWriter.writerow(self.row)

def toCsv(odsFilePath, csvTargetPath, dialect="excel"):
    assert odsFilePath is not None
    
    logging.getLogger("cutplace.ods").info("convert %r to %r" % (odsFilePath, csvTargetPath))
    zipArchive = zipfile.ZipFile(odsFilePath, "r")
    try:
        # TODO: Consider switching to 2.6 and use ZipFile.open(). This would need less memory.
        xmlData = zipArchive.read("content.xml")
    finally:
        zipArchive.close()

    csvTargetFile = open(csvTargetPath, "w")
    try:
        csvWriter = csv.writer(csvTargetFile, dialect)
        xml.sax.parseString(xmlData, OdsToCsvContentHandler(csvWriter))
    finally:
        csvTargetFile.close()
 
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger("cutplace.ods").setLevel(logging.INFO)
    if len(sys.argv) == 3:
        try:
            toCsv(sys.argv[1], sys.argv[2])
        except Exception, error:
            logging.getLogger("cutplace.ods").error("cannot convert ods to csv: %s" % str(error), exc_info=1)
    else:
        sys.stderr.write("Usage: %s {source.ods} {target.csv}%s" % (sys.argv[0], os.linesep))
