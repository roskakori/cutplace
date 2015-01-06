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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import sys

from cutplace import interface
from cutplace import errors
from cutplace import validator
from cutplace import iotools
from cutplace import _tools
# TODO #77: from cutplace import _web

from cutplace import __version__

DEFAULT_CID_ENCODING = 'utf-8'
DEFAULT_LOG_LEVEL = 'info'
assert DEFAULT_LOG_LEVEL in _tools.LOG_LEVEL_NAME_TO_LEVEL_MAP

_log = logging.getLogger("cutplace")


class CutplaceApp(object):
    """
    Command line application to validate CID's and data.
    """
    def __init__(self):
        self._log = _log
        self.cid = None
        self.cid_encoding = DEFAULT_CID_ENCODING
        self.cid_path = None
        self.is_split = False
        self.data_paths = None
        self.last_validation_was_ok = False
        self.is_web_server = False  # TODO #77: Remove.
        self.all_validations_were_ok = True

    def set_options(self, argv):
        """
        Reset options and set them again from argument list such as ``sys.argv[1:]``.
        """
        assert argv is not None

        description = 'validate DATA-FILE against interface description CID-FILE'
        version = '%(prog)s ' + __version__

        parser = argparse.ArgumentParser(description=description)
        parser.add_argument('--version', action='version', version=version)
        # TODO #77: parser.set_defaults(isLogTrace=False, isOpenBrowser=False, port=_web.DEFAULT_PORT)
        validation_group = parser.add_argument_group(
            'Validation options', 'Specify how to validate data and how to report the results')
        validation_group.add_argument(
            '-e', '--cid-encoding', metavar='ENCODING', dest='cid_encoding', default=DEFAULT_CID_ENCODING,
            help='character encoding to use when reading the CID (default: %s)' % DEFAULT_CID_ENCODING)
        validation_group.add_argument(
            '-P', '--plugins', metavar='FOLDER', dest='plugins_folder',
            help='folder to scan for plugins (default: no plugins)')
        # TODO: validationGroup.add_option('-s', '--split', action='store_true', dest='isSplit',
        #               help='split data in a CSV file containing the accepted rows and a raw text file '
        #               + 'containing rejected rows with both using UTF-8 as character encoding')
        # TODO #77: webGroup = optparse.OptionGroup(parser, 'Web options', 'Provide a  GUI for validation using a simple web server')
        # TODO #77: webGroup.add_option('-w', '--web', action='store_true', dest='isWebServer', help='launch web server')
        # TODO #77: webGroup.add_option('-p', '--port', metavar='PORT', type='int', dest='port', help='port for web server (default: %default)')
        # TODO #77: webGroup.add_option('-b', '--browse', action='store_true', dest='isOpenBrowser', help='open validation page in browser')
        # TODO #77: parser.add_option_group(webGroup)
        loggingGroup = parser.add_argument_group('Logging options', 'Modify the logging output')
        loggingGroup.add_argument(
            '--log', metavar='LEVEL', choices=sorted(_tools.LOG_LEVEL_NAME_TO_LEVEL_MAP.keys()), dest='log_level',
            default=DEFAULT_LOG_LEVEL, help='set log level to LEVEL (default: %s)' % DEFAULT_LOG_LEVEL)
        # TODO: loggingGroup.add_argument('-t', '--trace', action='store_true', dest='isLogTrace', help='include Python stack in error messages related to data')
        parser.add_argument(
            'cid_path', metavar='CID-FILE', help='file containing a cutplace interface definition (CID)')
        parser.add_argument(
            'data_paths', metavar='DATA-FILE', nargs=argparse.REMAINDER, help='data file(s) to validate')
        args = parser.parse_args(argv[1:])

        self._log.setLevel(_tools.LOG_LEVEL_NAME_TO_LEVEL_MAP[args.log_level])
        self.cid_encoding = args.cid_encoding
        # FIXME #77 etc: Remove dummy values below.
        self.isLogTrace = False
        # TODO #77: self.isOpenBrowser = False
        self.is_web_server = False  # TODO #77: Remove.
        # TODO #77: self.port = 0
        self.is_split = False
        # TODO: self.isLogTrace = self.options.isLogTrace
        # TODO: self.isOpenBrowser = self.options.isOpenBrowser
        # TODO #77: self.isWebServer = self.options.isWebServer
        # TODO #77: self.port = self.options.port
        # TODO: self.isSplit = self.options.isSplit

        if args.plugins_folder is not None:
            interface.import_plugins(args.plugins_folder)

        if not self.is_web_server:
            if args.cid_path is None:
                parser.error('CID-FILE must be specified')
            try:
                self.set_cid_from_path(args.cid_path)
            except (EnvironmentError, OSError) as error:
                raise IOError('cannot read CID file "%s": %s' % (args.cid_path, error))
        if args.data_paths is not None:
            self.data_paths = args.data_paths

        self._log.debug('cutplace %s', __version__)
        self._log.debug('arguments=%s', args)

    def set_cid_from_path(self, cid_path):
        assert cid_path is not None
        new_cid = interface.Cid()
        # TODO: if self.options is not None:
        #          new_cid.logTrace = self.options.isLogTrace
        _log.info('read CID from "%s"', cid_path)
        cid_rows = iotools.auto_rows(cid_path)  # TODO: Pass self.cid_encoding.
        new_cid.read(cid_path, cid_rows)
        self.cid = new_cid
        self.cid_path = cid_path

    def validate(self, data_path):
        """
        Validate data stored in file `data_path`.
        """
        assert data_path is not None
        assert self.cid is not None

        _log.info('validate "%s"', data_path)
        reader = validator.Reader(self.cid, data_path)
        try:
            reader.validate()
            _log.info('  accepted %d rows', reader.accepted_rows_count)
        except errors.CutplaceError as error:
            _log.error('  %s', error)
            self.all_validations_were_ok = False


def process(argv=None):
    """
    Do whatever the command line options ``argv`` request. In case of error, raise an appropriate
    `Exception`.

    Return 0 unless ``argv`` requested to validate one or more files and at least one of them
    contained rejected data. In this case, the result is 1.

    Before calling this, module ``logging`` has to be set up properly. For example, by calling
    `logging.basicConfig()`.
    """
    if argv is None:  # pragma: no cover
        argv = sys.argv
    assert argv

    result = 0
    cutplace_app = CutplaceApp()
    cutplace_app.set_options(argv)
    if cutplace_app.is_web_server:
        # TODO #77: _web.main(cutPlace.port, cutPlace.isOpenBrowser)
        pass
    elif cutplace_app.data_paths:
        for data_path in cutplace_app.data_paths:
            try:
                cutplace_app.validate(data_path)
            except (EnvironmentError, OSError) as error:
                raise EnvironmentError("cannot read data file %r: %s" % (data_path, error))
        if not cutplace_app.all_validations_were_ok:
            result = 1
    return result


def main(argv=None):
    """
    Main routine that logs errors and won't ``sys.exit()`` unless ``argv`` is broken.

    Before calling this, module ``logging`` has to be set up properly. For example, by calling
    ``logging.basicConfig()``.

    The result can be:
    * 0 - everything worked out fine
    * 1 - validation failed and rejected data must be fixed
    * 2 - arguments passed in ``argv`` must be fixed
    * 3 - a proper environment for the program to run must be provided (files must exist,
      access rights must be provided, ...)
    * 4 - something unexpected happened and the program code must be fixed
    """
    if argv is None:  # pragma: no cover
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
    except Exception as error:  # pragma: no cover
        result = 4
        _log.exception("cannot handle unexpected error: %s", error)
    return result


def main_for_script():  # pragma: no cover
    """
    Main routine that reports errors in options to `sys.stderr` and does `sys.exit()`.
    """
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())

if __name__ == '__main__':
    main_for_script()
