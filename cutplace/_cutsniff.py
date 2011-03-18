#!/usr/bin/env python
"""
Command line utility to create an interface control document
derived from sample data.
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
import logging
import optparse
import sys

import data
import sniff
import version
import _tools

_log = logging.getLogger("cutplace.cutsniff")

def main(argv=None):
    if argv is None:
        argv = sys.argv

    usage = """usage: %prog [options] ICDFILE DATAFILE
Write interface control document to ICDFILE describing the data found in
DATAFILE. The resulting ICD is stored in CSV format.

Example:
%prog --data-format=delimited --data-encoding iso-8859-15 icd_customers.csv some_customers.csv
   Analyze data file some_customers.csv assuming ISO-8859-15 as character
   encoding and store the resulting ICD in icd_customers.csv"""
    parser = optparse.OptionParser(usage=usage, version="%prog " + version.VERSION_TAG)
    parser.add_option("-d", "--icd-delimiter", default=',', metavar="DELIMITER", type="choice",
        choices=(",", ";"), dest="icdDelimiter",
        help="delimiter to separate rows in ICDFILE (default: %default)")
    parser.add_option("-e", "--data-encoding", default="ascii", metavar="ENCODING", dest="dataEncoding",
        help="character encoding to use when reading the data (default: %default)")
    parser.add_option("-f", "--data-format", default=sniff.FORMAT_AUTO, metavar="FORMAT", type="choice",
        choices=(sniff.FORMAT_AUTO, data.FORMAT_CSV, data.FORMAT_DELIMITED, data.FORMAT_EXCEL, data.FORMAT_ODS),
        dest="dataFormat", help="data format to assume for DATAFILE (default: %default)")
    parser.add_option("-a", "--stop-after", default=0, metavar="NUMBER", type="long",
        help="number of data rows after which to stop analyzing; 0=analyze all data (default: %default)")
    parser.add_option("-H", "--head", default=0, metavar="NUMBER", type="long",
        help="number of header rows to skip before to start analyzing (default: %default)")
    parser.add_option("--log", default=logging.getLevelName(logging.INFO).lower(), metavar="LEVEL", type="choice",
        choices=_tools.LogLevelNameToLevelMap.keys(), dest="logLevel",
        help="set log level to LEVEL (default: %default)")

    (options, others) = parser.parse_args(argv[1:])
    othersCount = len(others)
    if othersCount == 0:
        parser.error("ICDFILE and DATAFILE must be specified")
    elif othersCount == 1:
        parser.error("DATAFILE must be specified")
    elif othersCount > 2:
        parser.error("only ICDFILE and DATAFILE must be specified but also found: %s" % others[2:])

    icdPath = others[0]
    dataPath = others[1]
    exitCode = 1
    try:
        with open(icdPath, "wb") as icdFile:
            icdCsvWriter = _tools.UnicodeCsvWriter(
                icdFile, delimiter=options.icdDelimiter, encoding="ascii"
            )
            with open(dataPath, "rb") as dataFile:
                for icdRowToWrite in sniff.createInterfaceControlDocument(dataFile, dataFormat=options.dataFormat, encoding=options.dataEncoding):
                    icdCsvWriter.writerow(icdRowToWrite)
        exitCode = 0
    except EnvironmentError, error:
        _log.exception(error)
    except Exception, error:
        _log.exception(error)
    return exitCode

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
