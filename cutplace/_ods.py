#!/usr/bin/env python
"""
Read and convert ODS files created by OpenOffice.org's Calc.
"""
# Copyright (C) 2009-2013 Thomas Aglassinger
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
import argparse
import csv
import logging
import io
import sys
import threading
import xml.dom.minidom
import xml.sax
import zipfile

from cutplace import _tools

_log = logging.getLogger("cutplace.ods")


class AbstractOdsContentHandler(xml.sax.ContentHandler):
    """
    Sax ContentHandler for content.xml in ODS.
    """
    def __init__(self, sheet=1):
        assert sheet >= 1

        xml.sax.ContentHandler.__init__(self)
        self.tablesToSkip = sheet
        self._log = _log

    def startDocument(self):
        self.row = None
        self.cellText = None
        self.indent = 0
        self.insideCell = False

    def startElement(self, name, attributes):
        self.indent += 1
        if name == "table:table":
            self.tablesToSkip -= 1
            self._log.debug("%s<%s> #%d", " " * 2 * self.indent, name, self.tablesToSkip)
        elif (name == "table:table-cell") and (self.tablesToSkip == 0):
            try:
                self.numberColumnsRepeated = int(attributes.getValue("table:number-columns-repeated"))
            except KeyError:
                self.numberColumnsRepeated = 1
            self._log.debug("%s<%s> (%d) %r", " " * 2 * self.indent, name, self.numberColumnsRepeated, list(attributes.items()))
            self.insideCell = True
            self.cellText = ""
        elif (name == "table:table-row") and (self.tablesToSkip == 0):
            self._log.debug("%s<%s>", " " * 2 * self.indent, name)
            self.row = []

    def characters(self, text):
        if self.insideCell and (self.tablesToSkip == 0):
            self._log.debug("%s%r", " " * 2 * (self.indent + 1), text)
            self.cellText += text

    def endElement(self, name):
        if (name == "table:table-cell") and (self.tablesToSkip == 0):
            self._log.debug("%s</%s>", " " * 2 * self.indent, name)
            assert self.cellText is not None
            self.insideCell = False
            for _ in range(self.numberColumnsRepeated):
                cellType = type(self.cellText)
                assert cellType == str, "type(%r)=%r" % (self.cellText, cellType)
                self.row.append(self.cellText)
            self.cellText = None
        if (name == "table:table-row") and (self.tablesToSkip == 0):
            self._log.debug("%s</%s>", " " * 2 * self.indent, name)
            assert self.row is not None
            self.rowCompleted()
            self.row = None
        self.indent -= 1

    def rowCompleted(self):
        """
        Actions to be performed once ``self.row`` is complete and can be processed.
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
        except Exception as error:
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
        # FIXME: Add support for items containing line separators.
        if ("\n" in item) or ("\r" in item):
            raise NotImplementedError("item must not contain line separator: %r" % item)
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


def odsContent(source_ods_path):
    """
    Readable for content.xml in `source_ods_path`.
    """
    assert source_ods_path is not None

    with zipfile.ZipFile(source_ods_path, "r") as zip_archive:
        xml_data = zip_archive.read("content.xml")
        result = io.BytesIO(xml_data)

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
        raise ValueError("file must contain columns: \"%s\"" % odsFilePath)
    for columnIndex in range(len(lengths)):
        if lengths[columnIndex] == 0:
            raise ValueError("column %d in file %r must not always be empty" % (columnIndex + 1, odsFilePath))

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


# FIXME: The handlers for the various formats should support items spawning multiple columns.
# FIXME: Add support for items spawning multiple rows.


def main(arguments):
    assert arguments is not None

    _FORMAT_CSV = "csv"
    _FORMAT_RST = "rst"
    _FORMATS = [_FORMAT_CSV, _FORMAT_RST]
    _DEFAULT_FORMAT = _FORMAT_CSV
    _DEFAULT_SHEET = 1

    parser = argparse.ArgumentParser(description='convert ODS file to other formats')
    parser.add_argument("-f", "--format", metavar="FORMAT", default=_DEFAULT_FORMAT, choices=sorted(_FORMATS),
            dest="format",
            help="target format: %s (default: %s)" % (_tools.humanReadableList(_FORMATS), _DEFAULT_FORMAT))
    parser.add_argument("-1", "--heading", action="store_true", dest="firstRowIsHeading",
            help="render first row as heading")
    parser.add_argument("-s", "--sheet", metavar="SHEET", default=_DEFAULT_SHEET, type=int, dest="sheet",
            help="sheet to convert (default: %d)" % _DEFAULT_SHEET)
    parser.add_argument('source_ods_path', metavar='ODS-FILE', help='the ODS file to convert')
    parser.add_argument('target_path', metavar='TARGET-FILE', nargs='?', help='the target file to write')
    args = parser.parse_args(arguments)

    # Additional command line argument validation.
    if args.sheet < 1:
        parser.error("option --sheet is %d but must be at least 1" % args.sheet)
    if (args.format == _FORMAT_CSV) and args.firstRowIsHeading:
        parser.error("option --heading can not be used with --format=csv")

    if args.target_path is None:
        assert args.format in _FORMATS
        suffix = '.' + args.format
        args.target_path = _tools.withSuffix(args.source_ods_path, suffix)

    _log.info("convert %r to %r using format %r" % (args.source_ods_path, args.target_path, args.format))
    try:
        if args.format == _FORMAT_CSV:
            toCsv(args.source_ods_path, args.target_path, sheet=args.sheet)
        elif args.format == _FORMAT_RST:
            toRst(args.source_ods_path, args.target_path, firstRowIsHeading=args.firstRowIsHeading, sheet=args.sheet)
        else:  # pragma: no cover
            raise NotImplementedError("format=%r" % args.format)
    except EnvironmentError as error:
        _log.error("cannot convert ods: %s" % error)
        sys.exit(1)
    except Exception as error:
        _log.exception("cannot convert ods: %s" % error)
        sys.exit(1)

if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
