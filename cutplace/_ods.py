#!/usr/bin/env python
"""
Read and convert ODS files created by OpenOffice.org's Calc.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import csv
import logging
import optparse
import StringIO
import sys
import threading
import types
import xml.dom.minidom
import xml.sax
import zipfile

import _tools


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
            self._log.debug(u"%s<%s> #%d", " " * 2 * self.indent, name, self.tablesToSkip)
        elif (name == "table:table-cell") and (self.tablesToSkip == 0):
            try:
                self.numberColumnsRepeated = long(attributes.getValue("table:number-columns-repeated"))
            except KeyError:
                self.numberColumnsRepeated = 1
            self._log.debug(u"%s<%s> (%d) %r", " " * 2 * self.indent, name, self.numberColumnsRepeated, attributes.items())
            self.insideCell = True
            self.cellText = u""
        elif (name == "table:table-row") and (self.tablesToSkip == 0):
            self._log.debug(u"%s<%s>", " " * 2 * self.indent, name)
            self.row = []

    def characters(self, text):
        if self.insideCell and (self.tablesToSkip == 0):
            self._log.debug(u"%s%r", " " * 2 * (self.indent + 1), text)
            self.cellText += text

    def endElement(self, name):
        if (name == "table:table-cell") and (self.tablesToSkip == 0):
            self._log.debug(u"%s</%s>", " " * 2 * self.indent, name)
            assert self.cellText is not None
            self.insideCell = False
            for _ in range(self.numberColumnsRepeated):
                cellType = type(self.cellText)
                assert cellType == types.UnicodeType, u"type(%r)=%r" % (self.cellText, cellType)
                self.row.append(self.cellText)
            self.cellText = None
        if (name == "table:table-row") and (self.tablesToSkip == 0):
            self._log.debug(u"%s</%s>", " " * 2 * self.indent, name)
            assert self.row is not None
            self.rowCompleted()
            self.row = None
        self.indent -= 1

    def rowCompleted(self):
        """
        Actions to be performed once ``self.row`` is complete and can be processed.
        """
        raise NotImplementedError(u"rowCompleted must be implemented")


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
    ContentHandler to collect all rows in a list which can be accessed using the ``rows`` attribute.
    """
    def __init__(self, sheet=1):
        AbstractOdsContentHandler.__init__(self, sheet)
        self.rows = []

    def rowCompleted(self):
        self.rows.append(self.row)


class RowProducingContentHandler(AbstractOdsContentHandler):
    """
    ContentHandler to produce all rows to a target queue where a consumer in a different thread
    can get them.
    """
    def __init__(self, targetQueue, sheet=1):
        assert targetQueue is not None
        AbstractOdsContentHandler.__init__(self, sheet)
        self.queue = targetQueue

    def rowCompleted(self):
        self.queue.put(self.row)


def toCsv(odsFilePath, csvTargetPath, dialect="excel", sheet=1):
    """
    Convert ODS file in `odsFilePath` to CSV using `dialect` and store the result in `csvTargetPath`.
    """
    assert odsFilePath is not None
    assert csvTargetPath is not None
    assert dialect is not None
    assert sheet is not None
    assert sheet >= 1

    contentReadable = odsContent(odsFilePath)
    try:
        csvTargetFile = open(csvTargetPath, "w")
        try:
            csvWriter = csv.writer(csvTargetFile, dialect)
            xml.sax.parse(contentReadable, OdsToCsvContentHandler(csvWriter, sheet))
        finally:
            csvTargetFile.close()
    finally:
        contentReadable.close()


class ProducerThread(threading.Thread):
    """
    Thread to produce the contents of an ODS readable to a queue where a consumer can get it.

    Consumers should call ``Queue.get()`` until it returns ``None``. Possible exceptions raised
    in the background during `run()` are raised again when calling `join()` so no special means
    are necessary for the consumer to handle exceptions in the producer thread.
    """
    def __init__(self, readable, targetQueue, sheet=1):
        assert readable is not None
        assert targetQueue is not None
        assert sheet is not None
        assert sheet >= 1
        super(ProducerThread, self).__init__()
        self.readable = readable
        self.targetQueue = targetQueue
        self.sheet = sheet
        self.error = None

    def run(self):
        try:
            xml.sax.parse(self.readable, RowProducingContentHandler(self.targetQueue, self.sheet))
        except Exception, error:
            # Remember error information to raise it later during `join()`.
            self.error = error
        finally:
            # The last row always is a `None` to mark the end.
            self.targetQueue.put(None)

    def join(self):
        super(ProducerThread, self).join()
        if self.error is not None:
            raise self.error


def _writeRstRow(rstTargetFile, columnLengths, items):
    assert rstTargetFile is not None
    assert columnLengths
    assert items
    assert len(columnLengths) >= len(items)

    for columnIndex in range(len(columnLengths)):
        columnLength = columnLengths[columnIndex]
        if columnIndex < len(items):
            item = items[columnIndex]
        else:
            item = ""
        itemLength = len(item)
        assert columnLength >= itemLength
        # FIXME: Add support for items containing line separators .
        if ("\n" in item) or ("\r" in item):
            raise NotImplementedError(u"item must not contain line separator: %r" % item)
        rstTargetFile.write("+%s%s" % (item, " " * (columnLength - itemLength)))
    rstTargetFile.write("+\n")


def _writeRstSeparatorLine(rstTargetFile, columnLengths, lineSeparator):
    assert rstTargetFile is not None
    assert columnLengths
    assert lineSeparator in ["-", "="]

    for columnLength in columnLengths:
        rstTargetFile.write("+")
        if columnLength > 0:
            rstTargetFile.write(lineSeparator * columnLength)
    rstTargetFile.write("+\n")


def odsContent(odsSourceFilePath):
    """
    Readable for content.xml in `odsSourceFilePath`.
    """
    assert odsSourceFilePath is not None

    zipArchive = zipfile.ZipFile(odsSourceFilePath, "r")
    try:
        # TODO: Consider switching to 2.6 and use ZipFile.open(). This would need less memory.
        xmlData = zipArchive.read("content.xml")
        result = StringIO.StringIO(xmlData)
    finally:
        zipArchive.close()

    return result


def toRst(odsFilePath, rstTargetPath, firstRowIsHeading=True, sheet=1):
    """
    Convert ODS file in `odsFilePath` to reStructuredText and store the result in `rstTargetPath`.
    """
    assert odsFilePath is not None
    assert rstTargetPath is not None
    assert sheet >= 1

    rowListHandler = RowListContentHandler(sheet)
    readable = odsContent(odsFilePath)
    try:
        xml.sax.parse(readable, rowListHandler)
    finally:
        readable.close()

    # Find out the length of each column.
    lengths = []
    isFirstRow = True
    for row in rowListHandler.rows:
        for columnIndex in range(len(row)):
            item = row[columnIndex]
            itemLength = len(item)
            if isFirstRow or (columnIndex == len(lengths)):
                lengths.append(itemLength)
                isFirstRow = False
            elif lengths[columnIndex] < itemLength:
                lengths[columnIndex] = itemLength

    if not lengths:
        raise ValueError(u"file must contain columns: \"%s\"" % odsFilePath)
    for columnIndex in range(len(lengths)):
        if lengths[columnIndex] == 0:
            raise ValueError(u"column %d in file %r must not always be empty" % (columnIndex + 1, odsFilePath))

    rstTargetFile = open(rstTargetPath, "w")
    try:
        isFirstRow = firstRowIsHeading
        _writeRstSeparatorLine(rstTargetFile, lengths, "-")
        for row in rowListHandler.rows:
            _writeRstRow(rstTargetFile, lengths, row)
            if isFirstRow:
                lineSeparator = "="
                isFirstRow = False
            else:
                lineSeparator = "-"
            _writeRstSeparatorLine(rstTargetFile, lengths, lineSeparator)
    finally:
        rstTargetFile.close()


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


def toDocBookXml(odsFilePath, xmlTargetPath, xmlId, title, sheet=1):
    """
    Convert ODS file in `odsFilePath` to DocBook XML and store the result in `xmlTargetPath`.
    """
    assert odsFilePath is not None
    assert xmlTargetPath is not None
    assert xmlId is not None
    assert title is not None

    # Convert ODS to row list.
    handler = RowListContentHandler(sheet)
    contentReadable = odsContent(odsFilePath)
    try:
        xml.sax.parse(contentReadable, handler)
    finally:
        contentReadable.close()

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
    # TODO: Validate that `xmlId` is valid.
    table.setAttribute("xmlId", xmlId)
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

# FIXME: The handlers for the various formats should support items spawning multiple columns.
# FIXME: Add support for items spawning multiple rows.


def main(arguments):
    assert arguments is not None

    _FORMAT_CSV = "csv"
    _FORMAT_DOCBOOK = "docbook"
    _FORMAT_RST = "rst"
    _FORMATS = [_FORMAT_CSV, _FORMAT_DOCBOOK, _FORMAT_RST]
    _FORMAT_TO_SUFFIX_MAP = {
                             _FORMAT_CSV: ".csv",
                             _FORMAT_DOCBOOK: ".xml",
                             _FORMAT_RST: ".rst"
                             }
    usage = "usage: %prog [options] ODS-FILE [OUTPUT-FILE]"
    parser = optparse.OptionParser(usage)
    parser.set_defaults(format=_FORMAT_CSV, id="insert-id", sheet=1, title="Insert Title")
    parser.add_option("-f", "--format", metavar="FORMAT", type="choice", choices=_FORMATS, dest="format",
                      help="output format: %s (default: %%default)" % _tools.humanReadableList(_FORMATS))
    parser.add_option("-i", "--id", metavar="ID", dest="id", help="XML ID table can be referenced with (default: %default)")
    parser.add_option("-1", "--heading", action="store_true", dest="firstRowIsHeading", help="render first row as heading")
    parser.add_option("-s", "--sheet", metavar="SHEET", type="long", dest="sheet", help="sheet to convert (default: %default)")
    parser.add_option("-t", "--title", metavar="TITLE", dest="title", help="title to be used for XML table (default: %default)")
    options, others = parser.parse_args(arguments)

    # TODO: If no output file is specified, derive name from input file.
    log = logging.getLogger("cutplace.ods")
    if options.sheet < 1:
        log.error("option --sheet is %d but must be at least 1" % options.sheet)
        sys.exit(1)
    elif len(others) in [1, 2]:
        sourceFilePath = others[0]
        if len(others) == 2:
            targetFilePath = others[1]
        else:
            assert options.format in _FORMAT_TO_SUFFIX_MAP
            suffix = _FORMAT_TO_SUFFIX_MAP[options.format]
            targetFilePath = _tools.withSuffix(sourceFilePath, suffix)
        log.info("convert %r to %r using format %r" % (sourceFilePath, targetFilePath, options.format))
        try:
            if options.format == _FORMAT_CSV:
                if options.firstRowIsHeading:
                    log.error("option --heading can not be used with --format=csv")
                    sys.exit(1)
                toCsv(sourceFilePath, targetFilePath, sheet=options.sheet)
            elif options.format == _FORMAT_DOCBOOK:
                # FIXME: Add support for --heading with DocBook.
                assert not options.firstRowIsHeading
                toDocBookXml(sourceFilePath, targetFilePath, xmlId=options.id, title=options.title, sheet=options.sheet)
            elif options.format == _FORMAT_RST:
                toRst(sourceFilePath, targetFilePath, firstRowIsHeading=options.firstRowIsHeading, sheet=options.sheet)
            else:  # pragma: no cover
                raise NotImplementedError(u"format=%r" % (options.format))
        except EnvironmentError, error:
            logging.getLogger("cutplace.ods").error("cannot convert ods to csv: %s" % error)
            sys.exit(1)
        except Exception, error:
            logging.getLogger("cutplace.ods").error("cannot convert ods to csv: %s" % error, exc_info=1)
            sys.exit(1)
    else:
        log.error("ODS-FILE must be specified")
        sys.exit(1)

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig()
    logging.getLogger("cutplace.ods").setLevel(logging.INFO)
    main(sys.argv[1:])
