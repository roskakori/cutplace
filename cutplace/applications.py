#!/usr/bin/env python
"""
Front end for command line application. This takes care of parsing the
command line options, calling the appropriate low level function, reporting
any errors and setting a proper exit code to be passed to the end user.
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
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
import logging
import sys

from cutplace import __version__, _tools, errors, gui, interface, rowio, sql, validio

DEFAULT_CID_ENCODING = "utf-8"
DEFAULT_LOG_LEVEL = "info"
assert DEFAULT_LOG_LEVEL in _tools.LOG_LEVEL_NAME_TO_LEVEL_MAP
DEFAULT_VALIDATE_UNTIL = -1

_log = logging.getLogger("cutplace")


class CutplaceApp(object):
    """
    Command line application to validate CID's and data.
    """

    def __init__(self):
        """
        Setup the empty command line application.
        """
        self._log = _log
        self.cid = None
        self.cid_encoding = DEFAULT_CID_ENCODING
        self.cid_path = None
        self.is_gui = False
        self.is_create_sql = False
        self.data_paths = None
        self.last_validation_was_ok = False
        self.all_validations_were_ok = True
        self.validate_until = None

    def set_options(self, argv):
        """
        Reset options and set them again from argument list such as ``sys.argv[1:]``.
        """
        assert argv is not None

        description = "validate DATA-FILE against interface description CID-FILE"
        version = "%(prog)s " + __version__

        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            "--create",
            "-C",
            action="store_true",
            dest="is_create_sql",
            help="write SQL statement to create a table representing CID-FILE",
        )
        parser.add_argument(
            "--gui",
            "--g",
            action="store_true",
            dest="is_gui",
            help="provide a graphical user interface to set CID-FILE and DATA-FILE",
        )
        parser.add_argument(
            "--log",
            metavar="LEVEL",
            choices=sorted(_tools.LOG_LEVEL_NAME_TO_LEVEL_MAP.keys()),
            dest="log_level",
            default=DEFAULT_LOG_LEVEL,
            help="set log level to LEVEL (default: %s)" % DEFAULT_LOG_LEVEL,
        )
        parser.add_argument(
            "--plugins",
            "-P",
            metavar="FOLDER",
            dest="plugins_folder",
            help="folder to scan for plugins (default: no plugins)",
        )
        parser.add_argument(
            "--until",
            "-u",
            metavar="COUNT",
            dest="validate_until",
            default=DEFAULT_VALIDATE_UNTIL,
            type=int,
            help="maximum number of rows to validate; -1=all, 0=none (default: %d)" % DEFAULT_VALIDATE_UNTIL,
        )
        parser.add_argument("--version", action="version", version=version)
        parser.add_argument(
            "cid_path", metavar="CID-FILE", nargs="?", help="file containing a cutplace interface definition (CID)"
        )
        parser.add_argument("data_paths", metavar="DATA-FILE", nargs="*", help="data file(s) to validate")
        args = parser.parse_args(argv[1:])

        self._log.setLevel(_tools.LOG_LEVEL_NAME_TO_LEVEL_MAP[args.log_level])
        self.is_create_sql = args.is_create_sql
        self.is_gui = args.is_gui

        if args.validate_until is not None:
            if args.validate_until == -1:
                self.validate_until = None
            elif args.validate_until >= 0:
                self.validate_until = args.validate_until
            else:
                parser.error("option --until is %d but must be at least -1" % args.validate_until)
        if args.plugins_folder is not None:
            interface.import_plugins(args.plugins_folder)
        if args.data_paths is not None:
            self.data_paths = args.data_paths
        if args.is_gui:
            if not gui.has_tk:
                parser.error("tkinter package must be installed in order for --gui to work")
        if args.cid_path is not None:
            self.set_cid_from_path(args.cid_path)
        elif not args.is_gui:
            parser.error("CID_PATH or --gui must be specified")

        self._log.debug("cutplace %s", __version__)
        self._log.debug("arguments=%s", args)

    def set_cid_from_path(self, cid_path):
        """
        Read the :py:class:`cutplace.interface.Cid` to be used by this
        application from ``cid_path``.
        """
        assert cid_path is not None
        new_cid = interface.Cid()
        _log.info('read CID from "%s"', cid_path)
        cid_rows = rowio.auto_rows(cid_path)
        new_cid.read(cid_path, cid_rows)
        self.cid = new_cid
        self.cid_path = cid_path

    def validate(self, data_path):
        """
        Validate data stored in file ``data_path`` and log possible errors
        of type :py:exc:`cutplace.errors.CutplaceError` to the log.
        """
        assert data_path is not None
        assert self.cid is not None
        assert (self.validate_until is None) or (self.validate_until >= 0)

        _log.info('validate "%s"', data_path)

        try:
            with validio.Reader(self.cid, data_path, validate_until=self.validate_until) as reader:
                reader.validate_rows()
            _log.info("  accepted %d rows", reader.accepted_rows_count)
        except errors.CutplaceError as error:
            _log.error("  %s", error)
            self.all_validations_were_ok = False


def process(argv=None):
    """
    Do whatever the command line options ``argv`` request. In case of error,
    raise an appropriate :py:exc:`Exception`.

    Before calling this, module :py:mod:`logging` has to be set up properly.
    For example, by calling :py:func:`logging.basicConfig`.

    :return: 0 unless ``argv`` requested to validate one or more files and \
      at least one of them contained rejected data. In this case, the \
      result is 1.
    """
    if argv is None:  # pragma: no cover
        argv = sys.argv
    assert argv

    result = 0
    cutplace_app = CutplaceApp()
    cutplace_app.set_options(argv)
    if cutplace_app.is_gui:
        data_path = cutplace_app.data_paths[0] if len(cutplace_app.data_paths) >= 1 else None
        gui.open_gui(cutplace_app.cid_path, data_path)
    elif cutplace_app.is_create_sql:
        cid_reader = interface.Cid()
        sql.write_create(cutplace_app.cid_path, cid_reader)
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


if __name__ == "__main__":
    main_for_script()
