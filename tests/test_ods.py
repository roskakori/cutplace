"""
Tests for `_ods`.
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
import unittest

from tests import dev_test
from tests import _ods


class OdsTest(unittest.TestCase):
    def test_can_convert_ods_to_csv(self):
        source_ods_path = dev_test.path_to_test_data('valid_customers.ods')
        target_path = dev_test.path_to_test_result('valid_customers_from__ods.csv')
        _ods.main([source_ods_path, target_path])

    def test_can_convert_ods_to_rst(self):
        source_ods_path = dev_test.path_to_test_data('valid_customers.ods')
        target_path = dev_test.path_to_test_result('valid_customers_from__ods.rst')
        _ods.main(['--format=rst', source_ods_path, target_path])

    def test_fails_on_kinky_file_name(self):
        source_ods_path = dev_test.path_to_test_data('valid_customers.ods')
        target_path = dev_test.path_to_test_result('kinky_file_name//\\:^$\\::/')
        self.assertRaises(SystemExit, _ods.main, [source_ods_path, target_path])

    def test_fails_without_command_line_arguments(self):
        self.assertRaises(SystemExit, _ods.main, [])

    def test_fails_on_broken_sheet(self):
        source_ods_path = dev_test.path_to_test_data('valid_customers.ods')
        target_path = dev_test.path_to_test_result('valid_customers_from__ods.csv')
        self.assertRaises(SystemExit, _ods.main, ['--sheet=x', source_ods_path, target_path])
        self.assertRaises(SystemExit, _ods.main, ['--sheet=0', source_ods_path, target_path])
        self.assertRaises(SystemExit, _ods.main, ['--sheet=17', source_ods_path, target_path])


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    unittest.main()
