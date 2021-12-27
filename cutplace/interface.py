"""
Classes and functions to read and represent cutplace interface definitions.
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
import glob
import importlib.machinery
import importlib.util
import inspect
import io
import logging
import os.path
from pathlib import Path

from cutplace import _compat, _tools, checks, data, errors, fields, rowio

_log = logging.getLogger("cutplace")


class Cid(object):
    _EMPTY_INDICATOR = "x"
    _ID_CHECK = "c"
    _ID_DATA_FORMAT = "d"
    _ID_FIELD_RULE = "f"
    _VALID_IDS = [_ID_CHECK, _ID_DATA_FORMAT, _ID_FIELD_RULE]

    def __init__(self, cid_path=None):
        """
        Initialize a new CID with :py:attr:`~cutplace.interface.Cid.location`
        pointing to ``cid_path``, which can be one of the following:

        * a path to a file using CSV, Excel, or ODS as format; for CSV files,
          the delimiter is assumed to be a comma (,) and the encoding to be
          UTF-8 (which is backward compatible with ASCII).
        * ``None``, in which case location is automatically set to
          :py:func:`cutplace.errors.create_caller_location`.
        * an :py:class:`io.StringIO` containing a CSV
        """
        self._cid_path = cid_path
        self._data_format = None
        self._field_names = []
        self._field_formats = []
        self._field_name_to_format_map = {}
        self._field_name_to_index_map = {}
        self._check_names = []
        # TODO: Change to tuple(check_name, check).
        self._check_name_to_check_map = {}
        self._location = None
        self._check_name_to_class_map = Cid._create_name_to_class_map(checks.AbstractCheck)
        self._field_format_name_to_class_map = Cid._create_name_to_class_map(fields.AbstractFieldFormat)
        if cid_path is not None:
            self.read(cid_path, rowio.auto_rows(cid_path))
        else:
            self.set_location_to_caller()

    def __str__(self):
        result = "Cid("
        if self.data_format is not None:
            result += "format=" + self.data_format.format + "; "
            result += "fields=[%s]" % ", ".join(
                [
                    field_format.__class__.__name__ + "(" + field_format.field_name + ")"
                    for field_format in self.field_formats
                ]
            )
        return result

    def set_location_to_caller(self):
        """
        Set the internal :py:attr:`_location` to the caller function. This is
        useful for CID's that are created programmatically to provide at
        least some reference where possible errors in the CID originated from.

        It can be called repeatedly, for instance before each
        :py:meth:`add_check()` and :py:meth:`add_field_format()`.
        """
        self._location = errors.create_caller_location(["interface"], has_cell=True)

    @property
    def data_format(self):
        """
        The data format used by the this CID; refer to the
        :py:mod:`cutplace.data` module for possible formats.

        :rtype: cutplace.data.DataFormat
        """
        return self._data_format

    @property
    def field_names(self):
        """
        List of field names defined in this CID in the order they have been defined.
        """
        return self._field_names

    @property
    def field_formats(self):
        """
        List of field names defined in this CID in the order they have been defined.
        """
        return self._field_formats

    @property
    def check_names(self):
        """
        List of check names in no particular order.
        """
        return self._check_names

    @property
    def check_map(self):
        """
        Map of check names to the actual :py:class:`cutplace.checks.AbstractCheck`.
        """
        return self._check_name_to_check_map

    @staticmethod
    def _class_info(some_class):
        assert some_class is not None
        qualified_name = some_class.__module__ + "." + some_class.__name__
        source_path = Cid._class_source_path(some_class)
        result = qualified_name + ' (see: "' + source_path + '")'
        return result

    @staticmethod
    def _class_source_path(some_class):
        try:
            result = inspect.getsourcefile(some_class)
        except TypeError:
            result = "(internal)"
        return result

    @staticmethod
    def _is_ci_pytest_class(some_class):
        path_parts = Path(Cid._class_source_path(some_class)).parts
        return len(path_parts) >= 4 and path_parts[-4] == "cutplace" and path_parts[-2:] == ("bin", "pytest")

    @staticmethod
    def _create_name_to_class_map(base_class):
        assert base_class is not None
        result = {}
        # NOTE: we use a ``set`` of subclasses to ignore duplicates.
        for class_to_process in set(base_class.__subclasses__()):
            qualified_class_name = class_to_process.__name__
            plain_class_name = qualified_class_name.split(".")[-1]
            clashing_class = result.get(plain_class_name)
            if clashing_class is not None:
                clashing_class_info = Cid._class_info(clashing_class)
                class_to_process_info = Cid._class_info(class_to_process)
                if clashing_class_info == class_to_process_info:
                    # HACK: Ignore duplicate classes. Such classes can occur after `import_plugins`
                    #  has been called more than once.
                    class_to_process = None
                elif Cid._is_ci_pytest_class(class_to_process) or Cid._is_ci_pytest_class(clashing_class):
                    # HACK: Ignore duplicates during CI. There must be a better way to do this using
                    #  the pyproject.toml and build.yaml...
                    class_to_process = None
                else:
                    raise errors.CutplaceError(
                        "clashing plugin class names must be resolved: %s and %s"
                        % (clashing_class_info, class_to_process_info)
                    )
            if class_to_process is not None:
                result[plain_class_name] = class_to_process
        return result

    def _create_class(self, name_to_class_map, class_qualifier, class_name_appendix, type_name):
        assert name_to_class_map
        assert class_qualifier
        assert class_name_appendix
        assert type_name

        class_name = class_qualifier.split(".")[-1] + class_name_appendix
        result = name_to_class_map.get(class_name)
        if result is None:
            raise errors.InterfaceError(
                "cannot find class for %s %s: related class is %s but must be one of: %s"
                % (
                    type_name,
                    class_qualifier,
                    class_name,
                    _tools.human_readable_list(sorted(name_to_class_map.keys())),
                ),
                self._location,
            )
        return result

    def _create_field_format_class(self, field_type):
        assert field_type
        return self._create_class(self._field_format_name_to_class_map, field_type, "FieldFormat", "field")

    def _create_check_class(self, check_type):
        assert check_type
        return self._create_class(self._check_name_to_class_map, check_type, "Check", "check")

    def add_data_format_row(self, row_data):
        """
        Extract name and value from ``row_data`` and apply it to
        :py:attr:`~cutplace.interface.Cid.data_format` by calling
        :py:meth:`~cutplace.data.DataFormat.set_property`.

        :param list row_data: a list with at least 2 items for name and value \
            that can be passed to \
            :py:meth:`cutplace.data.DataFormat.set_property()`.
        """
        assert row_data is not None
        assert len(row_data) >= 2

        name, value = row_data[:2]
        lower_name = name.lower()
        self._location.advance_cell()
        if name == "":
            raise errors.InterfaceError("name of data format property must be specified", self._location)
        self._location.advance_cell()
        if (self._data_format is None) and (lower_name != data.KEY_FORMAT):
            raise errors.InterfaceError(
                "first data format row must set property %s instead of %s"
                % (_compat.text_repr(data.KEY_FORMAT), _compat.text_repr(name)),
                self._location,
            )
        if (self._data_format is not None) and (lower_name == data.KEY_FORMAT):
            raise errors.InterfaceError(
                "data format already is %s and must be set only once" % _compat.text_repr(self._data_format.format),
                self._location,
            )
        lower_value = value.lower()
        if self._data_format is None:
            self._data_format = data.DataFormat(lower_value, self._location)
        else:
            self._data_format.set_property(name.lower(), value, self._location)

    def read(self, cid_path, rows):
        """
        Provided no ``cid_path`` has already been specified for
        :py:class:`~cutplace.interface.Cid.__init__()`, process ``rows``
        using :py:meth:`~cutplace.interface.Cid.add_data_format_row()`,
        :py:meth:`~cutplace.interface.Cid.add_field_format()` and
        :py:meth:`~cutplace.interface.Cid.add_check()`. Report any errors by
        referring to ``cid_path``.

        :param str cid_path: the path from which ``rows`` where obtained
        :param sequence rows: sequence of lists where each list either \
          describes a data format, field format, check or comment for a CID.

        :raises cutplace.errors.InterfaceError: in case any row in ``rows`` \
          cannot be processed
        """
        assert cid_path is not None
        assert self.data_format is None, "CID must be read only once"

        # TODO: Detect format and use proper reader.
        self._location = errors.Location(cid_path, has_cell=True)
        if self._cid_path is None:
            self._cid_path = cid_path
        for row in rows:
            if row:
                row_type = row[0].lower().strip()
                row_data = (row[1:] + [""] * 6)[:6]
                if row_type == "d":
                    self.add_data_format_row(row_data)
                elif row_type == "f":
                    self.add_field_format_row(row_data)
                elif row_type == "c":
                    self.add_check_row(row_data)
                elif row_type != "":
                    # Raise error when value is not supported.
                    raise errors.InterfaceError(
                        'CID row type is "%s" but must be empty or one of: C, D, or F' % row_type, self._location
                    )
            self._location.advance_line()
        if self.data_format is None:
            raise errors.InterfaceError("data format must be specified", self._location)
        self.data_format.validate()
        if len(self.field_names) == 0:
            raise errors.InterfaceError("fields must be specified", self._location)

    def add_field_format(self, field_format):
        """
        Add field to the Cid. Typically the field is created using the
        constructor of any descendant of
        :py:class:`cutplace.fields.AbstractFieldFormat`. Alternatively it
        can be copied from existing :py:attr:`Cid.field_formats`.

        :param cutplace.fields.AbstractFieldFormat field_format: the field
            format to add
        :raises AssertionError: on violations of basic consistency, for
            example when attempting to add duplicate fields
        """
        assert self._data_format is not None
        assert field_format is not None
        field_name = field_format.field_name
        assert field_name is not None
        assert field_name not in self._field_name_to_format_map

        self._field_name_to_format_map[field_name] = field_format
        self._field_name_to_index_map[field_name] = len(self._field_names)
        self._field_names.append(field_name)
        self._field_formats.append(field_format)
        # TODO: Remember location where field format was defined to later include it in error message
        _log.debug("%s: defined field: %s", self._location, field_format)

    def add_field_format_row(self, possibly_incomplete_items):
        """
        Add field as described by `possibly_incomplete_items`, which is a
        list consisting of:

        1) field name
        2) optional: example value (can be empty)
        3) optional: empty flag ("X" = field is allowed to be empty)
        4) optional: length (using the syntax of :py:class:`cutplace.ranges.Range`)
        5) optional: field type (e.g. 'Integer' for :py:class:`cutplace.fields.IntegerFieldFormat`)
        6) optional: rule to validate field (depending on type)

        Any missing items are interpreted as empty string (``''``).
        Additional items are ignored.

        :raises cutplace.errors.InterfaceError: on broken \
          ``possibly_incomplete_items``
        """
        assert possibly_incomplete_items is not None
        assert self._location is not None

        if self._data_format is None:
            raise errors.InterfaceError("data format must be specified before first field", self._location)

        # Assert that the various lists and maps related to fields are in a consistent state.
        # Ideally this would be a class invariant, but this is Python, not Eiffel.
        field_count = len(self.field_names)
        assert len(self._field_formats) == field_count
        assert len(self._field_name_to_format_map) == field_count
        assert len(self._field_name_to_index_map) == field_count

        items = (possibly_incomplete_items + 6 * [""])[:6]

        # Obtain field name.
        field_name = fields.validated_field_name(items[0], self._location)
        if field_name in self._field_name_to_format_map:
            # TODO: Add see_also_location pointing to previous declaration.
            raise errors.InterfaceError(
                "duplicate field name must be changed to a unique one: %s" % field_name, self._location
            )

        # Obtain example.
        self._location.advance_cell()
        field_example = items[1]

        # Obtain "empty" mark.
        self._location.advance_cell()
        field_is_allowed_to_be_empty_text = items[2].strip().lower()
        if field_is_allowed_to_be_empty_text == "":
            field_is_allowed_to_be_empty = False
        elif field_is_allowed_to_be_empty_text == self._EMPTY_INDICATOR:
            field_is_allowed_to_be_empty = True
        else:
            raise errors.InterfaceError(
                "mark for empty field must be %s or empty but is %s"
                % (self._EMPTY_INDICATOR, field_is_allowed_to_be_empty_text),
                self._location,
            )

        # Obtain length.
        self._location.advance_cell()
        field_length = items[3]

        # Obtain field type and rule.
        self._location.advance_cell()
        field_type_item = items[4].strip()
        if field_type_item == "":
            field_type = "Text"
        else:
            field_type = ""
            field_type_parts = field_type_item.split(".")
            try:
                for part in field_type_parts:
                    if field_type:
                        field_type += "."
                    field_type += _tools.validated_python_name("field type part", part)
                assert field_type, "empty field type must be detected by validated_python_name()"
            except NameError as error:
                raise errors.InterfaceError(str(error), self._location)
        field_class = self._create_field_format_class(field_type)
        self._location.advance_cell()
        field_rule = items[5].strip()
        _log.debug("create field: %s(%r, %r, %r)", field_class.__name__, field_name, field_type, field_rule)
        try:
            field_format = field_class.__new__(
                field_class, field_name, field_is_allowed_to_be_empty, field_length, field_rule
            )
            field_format.__init__(field_name, field_is_allowed_to_be_empty, field_length, field_rule, self._data_format)
        except errors.InterfaceError as error:
            error_location = error.location if error.location is not None else self._location
            error.prepend_message("cannot declare field %s" % _compat.text_repr(field_name), error_location)
            raise error

        # Validate field length.
        # TODO #82: Cleanup validation for declared field formats.
        self._location.set_cell(4)
        field_length = field_format.length
        if self._data_format.format == data.FORMAT_FIXED:
            if field_length.items is None:
                raise errors.InterfaceError(
                    "length of field %s must be specified with fixed data format" % _compat.text_repr(field_name),
                    self._location,
                )
            if field_length.lower_limit != field_length.upper_limit:
                raise errors.InterfaceError(
                    "length of field %s for fixed data format must be a specific number but is: %s"
                    % (_compat.text_repr(field_name), field_format.length),
                    self._location,
                )
            if field_length.lower_limit < 1:
                raise errors.InterfaceError(
                    "length of field %s for fixed data format must be at least 1 but is: %d"
                    % (_compat.text_repr(field_name), field_format.length.lower_limit),
                    self._location,
                )
        elif field_length.lower_limit is not None:
            if field_length.lower_limit < 0:
                raise errors.InterfaceError(
                    "lower limit for length of field %s must be at least 0 but is: %d"
                    % (_compat.text_repr(field_name), field_format.length.lower_limit),
                    self._location,
                )
        elif field_length.upper_limit is not None:
            # Note: 0 as upper limit is valid for a field that must always be empty.
            if field_length.upper_limit < 0:
                raise errors.InterfaceError(
                    "upper limit for length of field %s must be at least 0 but is: %d"
                    % (_compat.text_repr(field_name), field_format.length.upper_limit),
                    self._location,
                )

        # Set and validate example in case there is one.
        if field_example != "":
            try:
                field_format.example = field_example
            except errors.FieldValueError as error:
                self._location.set_cell(2)
                raise errors.InterfaceError(
                    "cannot validate example for field %s: %s" % (_compat.text_repr(field_name), error), self._location
                )

        self._location.set_cell(1)

        assert field_name
        assert field_type
        assert field_rule is not None

        self.add_field_format(field_format)

    def add_check(self, check_to_add):
        """
        Add ``check_to_add`` to the Cid so it can be performed during
        validation.

        :param cutplace.checks.AbstractCheck check_to_add: the check to add
        """
        assert check_to_add.descrption not in self._check_name_to_check_map

        self._check_name_to_check_map[check_to_add.description] = check_to_add
        self._check_names.append(check_to_add.description)
        assert len(self.check_names) == len(self._check_name_to_check_map)

    def add_check_row(self, possibly_incomplete_items):
        """
        Add a check as declared in ``possibly_incomplete_items``, which
        ideally is a list composed of 3 elements:

        1. description ('customer_id_must_be_unique')
        2. type (e.g. 'IsUnique'  mapping to :py:class:`cutplace.checks.IsUniqueCheck`)
        3. rule (e.g. 'customer_id')

        Missing items are interpreted as empty string (``''``), additional
        items are ignored.

        :raises cutplace.errors.InterfaceError: on broken \
          ``possibly_incomplete_items``
        """
        assert possibly_incomplete_items is not None

        items = list(possibly_incomplete_items)
        # HACK: Ignore possible concatenated (empty) cells between description and type.
        while (len(items) >= 2) and (items[1].strip() == ""):
            del items[1]

        check_description, check_type, check_rule = (items + 3 * [""])[:3]
        self._location.advance_cell()
        if check_description == "":
            raise errors.InterfaceError("check description must be specified", self._location)
        self._location.advance_cell()
        check_class_name = check_type + "Check"
        if check_class_name not in self._check_name_to_class_map:
            list_of_available_check_types = _tools.human_readable_list(sorted(self._check_name_to_class_map.keys()))
            raise errors.InterfaceError(
                "check type is '%s' but must be one of: %s" % (check_type, list_of_available_check_types),
                self._location,
            )
        _log.debug("create check: %s(%r, %r)", check_type, check_description, check_rule)
        check_class = self._create_check_class(check_type)
        check = check_class.__new__(check_class, check_description, check_rule, self._field_names, self._location)
        check.__init__(check_description, check_rule, self._field_names, self._location)
        self._location.set_cell(1)
        existing_check = self._check_name_to_check_map.get(check_description)
        if existing_check is not None:
            raise errors.InterfaceError(
                "check description must be used only once: %s" % _compat.text_repr(check_description),
                self._location,
                "first declaration",
                existing_check.location,
            )
        self._check_name_to_check_map[check_description] = check
        self._check_names.append(check_description)
        assert len(self.check_names) == len(self._check_name_to_check_map)

    def field_index(self, field_name):
        """
        The column index of  the field named ``field_name`` starting with 0.
        """
        assert field_name in self._field_name_to_index_map, "unknown field name '%s' must be replaced by one of: %s" % (
            field_name,
            _tools.human_readable_list(sorted(self.field_names)),
        )

        return self._field_name_to_index_map[field_name]

    def field_value_for(self, field_name, row):
        """
        The value for field ``field_name`` in ``row``.

        :param list row: the row to obtain the :py:class:`str` value for \
          ``field_name`` from

        :raises AssertionError: if ``field_name`` is not part of the CID
        :raises AssertionError: if ``row`` does not have the expected number of items
        """
        assert field_name in self._field_name_to_index_map, "unknown field name %r must be replaced by one of: %s" % (
            field_name,
            _tools.human_readable_list(sorted(self.field_names)),
        )
        assert row is not None
        actual_row_count = len(row)
        expected_row_count = len(self.field_names)
        assert actual_row_count == expected_row_count, "row must have %d items but has %d: %s" % (
            expected_row_count,
            actual_row_count,
            row,
        )

        return row[self._field_name_to_index_map[field_name]]

    def field_format_for(self, field_name):
        """
        The :py:class:`cutplace.fields.AbstractFieldFormat` for
        ``field_name``.

        :raises KeyError: on unknown ``field_name``
        """
        return self._field_name_to_format_map[field_name]

    def check_for(self, check_name):
        """
        The :py:class:`cutplace.checks.AbstractCheck` for ``check_name``.

        :raises KeyError: on unknown ``check_name``
        """
        assert check_name is not None
        return self._check_name_to_check_map[check_name]


def create_cid_from_string(cid_text):
    """
    A :py:class:`~cutplace.interface.Cid` as described in ``cid_text``
    using CSV format with comma (,) as delimiter (factory function).
    """
    with io.StringIO(cid_text) as cid_string_io:
        result = Cid(cid_string_io)
    return result


def field_names_and_lengths(fixed_cid):
    """
    List of tuples ``(field_name, field_length)`` for all field formats in
    ``fixed_cid`` which must be of data format
    :py:attr:`~cutplace.data.FORMAT_FIXED`. Here, ``field_length`` is an
    ``int`` derived from
    :py:attr:`~cutplace.fields.AbstractFieldFormat.length`.
    """
    assert fixed_cid is not None
    assert fixed_cid.data_format.format == data.FORMAT_FIXED, "format=" + fixed_cid.data_format.format
    result = []
    for field_format in fixed_cid.field_formats:
        field_name = field_format.field_name
        assert len(field_format.length.items) == 1
        field_length_range = field_format.length.items[0]
        lower, upper = field_length_range
        assert lower is not None
        assert lower == upper
        field_length = lower
        result.append((field_name, field_length))
    return result


def import_plugins(folder_to_scan_for_plugins):
    """
    Import all Python modules found in folder
    ``folder_to_scan_for_plugins`` (non recursively) consequently making the
    contained field formats and checks available for CIDs.
    """

    def log_imported_items(item_name, base_set, current_set):
        new_items = [item.__name__ for item in (current_set - base_set)]
        _log.info("    %s found: %s", item_name, new_items)

    _log.info('import plugins from "%s"', folder_to_scan_for_plugins)
    modules_to_import = set()
    base_checks = set(checks.AbstractCheck.__subclasses__())  # @UndefinedVariable
    base_field_formats = set(fields.AbstractFieldFormat.__subclasses__())  # @UndefinedVariable
    pattern_to_scan = os.path.join(folder_to_scan_for_plugins, "*.py")
    for module_to_import_path in glob.glob(pattern_to_scan):
        module_name = os.path.splitext(os.path.basename(module_to_import_path))[0]
        modules_to_import.add((module_name, module_to_import_path))
    for module_name_to_import, module_path_to_import in modules_to_import:
        _log.info("  import %s from '%s'", module_name_to_import, module_path_to_import)
        module_path_to_import = os.path.abspath(module_path_to_import)
        loader = importlib.machinery.SourceFileLoader(module_name_to_import, module_path_to_import)
        spec = importlib.util.spec_from_loader(module_name_to_import, loader)
        loaded_module = importlib.util.module_from_spec(spec)
        loader.exec_module(loaded_module)
    current_checks = set(checks.AbstractCheck.__subclasses__())  # @UndefinedVariable
    current_field_formats = set(fields.AbstractFieldFormat.__subclasses__())  # @UndefinedVariable
    log_imported_items("fields", base_field_formats, current_field_formats)
    log_imported_items("checks", base_checks, current_checks)
