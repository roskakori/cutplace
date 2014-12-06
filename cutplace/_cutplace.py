#!/usr/bin/env python
"""
Cutplace - Validate flat data according to an interface control document.
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
import encodings
import glob
import io
import logging
import os
import sys
import xlrd

from cutplace import cid
from cutplace import errors
from cutplace import validator
from cutplace import _tools
# TODO: from cutplace import _web

# Import constant for version information.
from cutplace import __version__

DEFAULT_ICD_ENCODING = 'utf-8'
DEFAULT_LOG_LEVEL = 'warning'
assert DEFAULT_LOG_LEVEL in _tools.LOG_LEVEL_NAME_TO_LEVEL_MAP

_log = logging.getLogger("cutplace")


def _openForWriteUsingUtf8(targetPath):
    assert targetPath is not None
    return io.open(targetPath, 'w', encoding="utf-8")


class CutPlace(object):
    """
    Command line interface for CutPlace.
    """
    def __init__(self):
        self._log = logging.getLogger("cutplace")
        self.options = None
        self.icd = None
        self.icdEncoding = DEFAULT_ICD_ENCODING
        self.icdPath = None
        self.isSplit = False
        self.dataToValidatePaths = None
        self.lastValidationWasOk = False

    def setOptions(self, argv):
        """Reset options and set them again from argument list such as sys.argv[1:]."""
        assert argv is not None

        description = 'validate DATA-FILE against interface description CID-FILE'
        version = '%(prog)s ' + __version__

        parser = argparse.ArgumentParser(description=description)
        parser.add_argument('--version', action='version', version=version)
        # TODO: parser.set_defaults(isLogTrace=False, isOpenBrowser=False, port=_web.DEFAULT_PORT)
        # TODO: parser.add_option('--list-encodings', action='store_true', dest='isShowEncodings', help='show list of available character encodings and exit')
        validation_group = parser.add_argument_group('Validation options', 'Specify how to validate data and how to report the results')
        validation_group.add_argument('-e', '--cid-encoding', metavar='ENCODING', dest='cid_encoding',
            default=DEFAULT_ICD_ENCODING,
            help='character encoding to use when reading the CID (default: %s)' % DEFAULT_ICD_ENCODING)
        validation_group.add_argument('-P', '--plugins', metavar='FOLDER', dest='plugins_folder',
            help='folder to scan for plugins (default: no plugins)')
        # TODO: validationGroup.add_option('-s', '--split', action='store_true', dest='isSplit',
        #               help='split data in a CSV file containing the accepted rows and a raw text file '
        #               + 'containing rejected rows with both using UTF-8 as character encoding')
        # TODO: webGroup = optparse.OptionGroup(parser, 'Web options', 'Provide a  GUI for validation using a simple web server')
        # TODO: webGroup.add_option('-w', '--web', action='store_true', dest='isWebServer', help='launch web server')
        # TODO: webGroup.add_option('-p', '--port', metavar='PORT', type='int', dest='port', help='port for web server (default: %default)')
        # TODO: webGroup.add_option('-b', '--browse', action='store_true', dest='isOpenBrowser', help='open validation page in browser')
        # TODO: parser.add_option_group(webGroup)
        loggingGroup = parser.add_argument_group('Logging options', 'Modify the logging output')
        loggingGroup.add_argument('--log', metavar='LEVEL', choices=sorted(_tools.LOG_LEVEL_NAME_TO_LEVEL_MAP.keys()),
            dest='log_level', default=DEFAULT_LOG_LEVEL,
            help='set log level to LEVEL (default: %s)' % DEFAULT_LOG_LEVEL)
        # TODO: loggingGroup.add_argument('-t', '--trace', action='store_true', dest='isLogTrace', help='include Python stack in error messages related to data')
        parser.add_argument('cid_path', metavar='CID-FILE', help='file containing a cutplace interface definition (CID)')
        parser.add_argument('data_paths', metavar='DATA-FILE', nargs=argparse.REMAINDER, help='data file(s) to validate')
        args = parser.parse_args(argv[1:])

        self._log.setLevel(_tools.LOG_LEVEL_NAME_TO_LEVEL_MAP[args.log_level])
        self.cid_encoding = args.cid_encoding
        # FIXME: Remove dummy values below.
        self.isLogTrace = False
        self.isOpenBrowser = False
        self.isShowEncodings = False
        self.isWebServer = False
        self.port = 0
        self.isSplit = False
        # TODO: self.isLogTrace = self.options.isLogTrace
        # TODO: self.isOpenBrowser = self.options.isOpenBrowser
        # TODO: self.isShowEncodings = self.options.isShowEncodings
        # TODO: self.isWebServer = self.options.isWebServer
        # TODO: self.port = self.options.port
        # TODO: self.isSplit = self.options.isSplit

        if args.plugins_folder is not None:
            cid.import_plugins(args.plugins_folder)

        if not self.isShowEncodings and not self.isWebServer:
            if args.cid_path is None:
                parser.error('CID-PATH must be specified')
            try:
                self.setIcdFromFile(args.cid_path)
            except (EnvironmentError, OSError) as error:
                raise IOError('cannot read CID file "%s": %s' % (args.cid_path, error))
            if args.data_paths is not None:
                self.dataToValidatePaths = args.data_paths

        self._log.debug('cutplace %s', __version__)
        self._log.debug('arguments=%s', args)

    def validate(self, dataFilePath):
        """
        Validate data stored in file `dataFilePath`.
        """
        assert dataFilePath is not None
        assert self.icd is not None

        self.lastValidationWasOk = False
        reader = validator.Reader(self.icd, dataFilePath)
        reader.validate()
        self.lastValidationWasOk = True

    def setIcdFromFile(self, cid_path):
        assert cid_path is not None
        new_cid = cid.Cid()
        # TODO: if self.options is not None:
        #          new_cid.logTrace = self.options.isLogTrace
        cid_rows = cid.auto_rows(cid_path)  # TODO: Pass self.cid_encoding.
        new_cid.read(cid_path, cid_rows)
        self.icd = new_cid
        self.icdPath = cid_path

    def _printAvailableEncodings(self):
        for encoding in self._encodingsFromModuleNames():
            if encoding != "__init__":
                print(encoding)

    def _encodingsFromModuleNames(self):
        # Based on sample code by Peter Otten.
        encodingsModuleFilePath = os.path.dirname(encodings.__file__)
        for filePath in glob.glob(os.path.join(encodingsModuleFilePath, "*.py")):
            fileName = os.path.basename(filePath)
            yield os.path.splitext(fileName)[0]


def process(argv=None):
    """
    Do whatever the command line options ``argv`` request. In case of error, raise an appropriate
    ``Exception``.

    Return 0 unless ``argv`` requested to validate one or more files and at least one of them
    contained rejected data. In this case, the result is 1.

    Before calling this, module ``logging`` has to be set up properly. For example, by calling
    ``logging.basicConfig()``.
    """
    if argv is None:
        argv = sys.argv
    assert argv

    result = 0
    cutPlace = CutPlace()
    cutPlace.setOptions(argv)
    if cutPlace.isShowEncodings:
        cutPlace._printAvailableEncodings()
    else:
        if cutPlace.isWebServer:
            _web.main(cutPlace.port, cutPlace.isOpenBrowser)
        elif cutPlace.dataToValidatePaths:
            allValidationsOk = True
            for path in cutPlace.dataToValidatePaths:
                try:
                    cutPlace.validate(path)
                    if not cutPlace.lastValidationWasOk:
                        allValidationsOk = False
                except EnvironmentError as error:
                    raise EnvironmentError("cannot read data file %r: %s" % (path, error))
            if not allValidationsOk:
                result = 1
    return result


def main(argv=None):
    """
    Main routine that might raise errors but won't ``sys.exit()`` unless ``argv`` is broken.

    Before calling this, module ``logging`` has to be set up properly. For example, by calling
    ``logging.basicConfig()``.
    """
    if argv is None:
        argv = sys.argv
    assert argv

    result = 1
    try:
        result = process(argv)
    except (EnvironmentError, OSError) as error:
        result = 3
        _log.error("%s", error)
    except errors.CutplaceError as error:
        _log.error("%s", error)
    except Exception as error:
        result = 4
        _log.exception("cannot handle unexpected error: %s", error)
    return result


def main_for_script():
    """
    Main routine that reports errors in options to ``sys.stderr`` and does ``sys.exit()``.
    """
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())

if __name__ == '__main__':
    main_for_script()
