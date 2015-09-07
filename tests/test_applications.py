"""
Tests for cutplace application.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
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

import logging
import os
import unittest

import six

from cutplace import applications
from tests import dev_test
from tests import _ods


_log = logging.getLogger("cutplace.test_applications")

_customers_cid_path = dev_test.path_to_example('cid_customers.ods')
_valid_customers_csv_path = dev_test.path_to_example('customers.csv')


def _assert_valid_customers_has_no_barret():
    import io
    with io.open(_valid_customers_csv_path, 'r', encoding='cp1252') as customers_file:
        customers_content = customers_file.read()
    assert 'Barret' not in customers_content


class CutplaceAppTest(unittest.TestCase):
    def setUp(self):
        self._cutplace_app = applications.CutplaceApp()
        self._cutplace_app.set_cid_from_path(_customers_cid_path)
        self._broken_customers_non_csv_path = dev_test.path_to_test_data('valid_customers.ods')
        _assert_valid_customers_has_no_barret()

    def test_can_validate_csv(self):
        self._cutplace_app.validate(_valid_customers_csv_path)
        self.assertTrue(self._cutplace_app.all_validations_were_ok)

    def test_can_validate_csv_multiple_times(self):
        for _ in range(5):
            self._cutplace_app.validate(_valid_customers_csv_path)
        self.assertTrue(self._cutplace_app.all_validations_were_ok)

    def test_can_detect_unmatched_data_format(self):
        self._cutplace_app.validate(self._broken_customers_non_csv_path)
        self.assertFalse(self._cutplace_app.all_validations_were_ok)

    def test_can_validate_after_error(self):
        self.test_can_detect_unmatched_data_format()
        self._cutplace_app.validate(_valid_customers_csv_path)
        self.assertFalse(self._cutplace_app.all_validations_were_ok)


class CutplaceProcessTest(unittest.TestCase):
    """
    Test cases for `_cutplace.process`.
    """
    def setUp(self):
        # _assert_valid_customers_has_no_barret()
        pass

    def _test_process_exits_with(self, arguments, expected_exit_code):
        try:
            applications.process(['test_applications.py'] + arguments)
            self.fail('SystemExit expected')
        except SystemExit as expected_error:
            self.assertEqual(expected_exit_code, expected_error.code)

    def test_can_show_version(self):
        self._test_process_exits_with(['--version'], 0)

    def test_can_show_help(self):
        self._test_process_exits_with(['--help'], 0)
        self._test_process_exits_with(['--h'], 0)

    def _test_can_read_cid(self, suffix):
        cid_path = dev_test.path_to_test_cid('cid_customers.' + suffix)
        exit_code = applications.process(['test_can_read_valid_' + suffix + '_cid', cid_path])
        self.assertEqual(0, exit_code)

    def test_can_read_csv_cid(self):
        source_ods_cid_path = dev_test.path_to_test_cid('cid_customers.ods')
        target_csv_cid_path = dev_test.path_to_test_cid('cid_customers.csv')
        _ods.to_csv(source_ods_cid_path, target_csv_cid_path)
        self._test_can_read_cid('csv')
        os.remove(target_csv_cid_path)

    def test_can_read_ods_cid(self):
        self._test_can_read_cid('ods')

    def test_can_read_excel_cid(self):
        self._test_can_read_cid('xls')

    def test_fails_on_non_existent_cid(self):
        self.assertRaises(IOError, applications.process, ['test_fails_on_non_existent_cid', 'no_such_cid.xls'])

    def test_can_validate_proper_csv(self):
        cid_path = dev_test.CID_CUSTOMERS_ODS_PATH
        csv_path = dev_test.CUSTOMERS_CSV_PATH
        exit_code = applications.process(['test_can_validate_proper_csv', cid_path, csv_path])
        self.assertEqual(0, exit_code)

    def test_can_read_cid_with_plugins(self):
        cid_path = dev_test.path_to_example('cid_colors.ods')
        exit_code = applications.process(
            ['test_can_read_cid_with_plugins', '--plugins', dev_test.path_to_test_plugins(), cid_path])
        self.assertEqual(0, exit_code)

    def test_can_validate_csv_with_plugins(self):
        cid_path = dev_test.path_to_example('cid_colors.ods')
        csv_path = dev_test.path_to_example('colors.csv')
        exit_code = applications.process([
            'test_can_validate_proper_csv_with_plugins', '--plugins', dev_test.path_to_test_plugins(),
            cid_path, csv_path])
        self.assertEqual(0, exit_code)

    def test_fails_on_broken_csv_with_plugins(self):
        cid_path = dev_test.path_to_example('cid_colors.ods')
        csv_path = dev_test.path_to_example('colors_broken.csv')
        exit_code = applications.process([
            'test_can_validate_proper_csv_with_plugins', '--plugins', dev_test.path_to_test_plugins(),
            cid_path, csv_path])
        self.assertEqual(1, exit_code)

    def test_fails_on_non_existent_data(self):
        if six.PY2:
            expected_error_class = EnvironmentError
        else:
            expected_error_class = IOError
        cid_path = dev_test.path_to_test_cid('customers.xls')
        self.assertRaises(expected_error_class, applications.process, ['test_fails_on_non_existent_data', cid_path, 'no_such_data.csv'])

    def test_fails_on_unknown_command_line_argument(self):
        self._test_process_exits_with(['--no-such-option'], 2)

    def test_fails_without_any_command_line_argument(self):
        self._test_process_exits_with([], 2)

    # TODO: Migrate test cases below.
    # def testValidCsvs(self):
    #     VALID_PREFIX = 'valid_'
    #     testsInputFolder = dev_test.path_to_test_folder('input')
    #     validCsvFileNames = _tools.listdirMatching(testsInputFolder, VALID_PREFIX + '.*\\.csv', '.*with_head.*')
    #     validCsvPaths = list(os.path.join(testsInputFolder, fileName) for fileName in validCsvFileNames)
    #     for dataPath in validCsvPaths:
    #         # Compute the base name of the related CID.
    #         baseFileName = os.path.basename(dataPath)
    #         baseFileNameWithoutCsvSuffix = os.path.splitext(baseFileName)[0]
    #         baseFileNameWithoutValidPrefixAndCsvSuffix = baseFileNameWithoutCsvSuffix[len(VALID_PREFIX):]
    #         # Compute the full path of the related CID.
    #         icdBaseName = baseFileNameWithoutValidPrefixAndCsvSuffix.split('_')[0]
    #         icdPath = dev_test.path_to_test_cid(icdBaseName + '.csv')
    #         if not os.path.exists(icdPath):
    #             icdPath = dev_test.path_to_test_cid(icdBaseName + '.ods')
    #             self.assertTrue(os.path.exists(icdPath),
    #                     'icd '%s' (or '*.csv') for data file '%s' must be created' % (icdPath, dataPath))
    #
    #         # Now validate the data.
    #         exitCode = _cutplace.main(['test_applications.py', icdPath, dataPath])
    #         self.assertEqual(exitCode, 0)
    #
    # def testValidFixedTxt(self):
    #     icdPath = dev_test.path_to_test_cid('customers_fixed.ods')
    #     dataPath = dev_test.path_to_test_data('valid_customers_fixed.txt')
    #     exitCode = _cutplace.main(['test_applications.py', icdPath, dataPath])
    #     self.assertEqual(exitCode, 0)
    #
    # def testValidNativeExcelFormats(self):
    #     icdPath = dev_test.path_to_test_cid('native_excel_formats.ods')
    #     dataPath = dev_test.path_to_test_data('valid_native_excel_formats.xls')
    #     exitCode = _cutplace.main(['test_applications.py', icdPath, dataPath])
    #     self.assertEqual(exitCode, 0)


class CutplaceMainTest(unittest.TestCase):
    """
    Test cases for cutplace command line interface in `_cutplace.main()`.
    """
    def test_can_read_cid(self):
        self.assertEqual(0, applications.main(['test', _customers_cid_path]))

    def test_can_validate_proper_data(self):
        self.assertEqual(0, applications.main(['test', _customers_cid_path, _valid_customers_csv_path]))

    def test_can_deal_with_broken_data(self):
        data_path = dev_test.path_to_test_data('broken_customers.csv')
        self.assertEqual(1, applications.main(['test', _customers_cid_path, data_path]))

    def test_can_deal_with_broken_cid(self):
        broken_cid_path = dev_test.path_to_test_cid('broken_syntax_error.ods')
        self.assertEqual(1, applications.main(['test', broken_cid_path]))

    def test_can_deal_with_non_existent_cid(self):
        self.assertEqual(3, applications.main(['test', 'no_such_cid.xxx']))

    def test_can_deal_with_non_existent_data(self):
        self.assertEqual(3, applications.main(['test', _customers_cid_path, 'no_such_data.xxx']))

    def _test_fails_with_system_exit(self, expected_code, argv):
        try:
            applications.main(argv)
            self.fail()
        except SystemExit as anticipated_error:
            self.assertEqual(expected_code, anticipated_error.code)

    def test_can_show_help(self):
        self._test_fails_with_system_exit(0, ['test', '--help'])

    def test_can_show_version(self):
        self._test_fails_with_system_exit(0, ['test', '--version'])

    def test_fails_without_any_arguments(self):
        self._test_fails_with_system_exit(2, ['test'])


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
