"""
Test for `_tools` module.
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

import os.path
import random
import unittest

from cutplace import _tools
from tests import dev_test


class ToolsTest(unittest.TestCase):
    def test_can_create_test_date_time(self):
        randomizer = random.Random(0)
        for _ in range(15):
            random_datetime = dev_test.random_datetime(randomizer)
            self.assertTrue(random_datetime is not None)
            self.assertNotEqual(random_datetime, '')

    def test_can_create_test_name(self):
        randomizer = random.Random(0)
        for _ in range(15):
            name = dev_test.random_name(randomizer)
            self.assertTrue(name is not None)
            self.assertNotEqual(name, '')

    def test_can_create_test_customer_row(self):
        for customer_id in range(15):
            row = dev_test.create_test_customer_row(customer_id)
            self.assertTrue(row is not None)
            self.assertEqual(len(row), 5)

    def test_can_validate_python_name(self):
        self.assertEqual(_tools.validated_python_name('x', 'abc_123'), 'abc_123')
        self.assertEqual(_tools.validated_python_name('x', ' abc_123 '), 'abc_123')
        self.assertRaises(NameError, _tools.validated_python_name, 'x', '1337')
        self.assertRaises(NameError, _tools.validated_python_name, 'x', '')
        self.assertRaises(NameError, _tools.validated_python_name, 'x', ' ')
        self.assertRaises(NameError, _tools.validated_python_name, 'x', 'a.b')

    def test_can_build_human_readable_list(self):
        self.assertEqual(_tools.human_readable_list([]), '')
        self.assertEqual(_tools.human_readable_list(['a']), "'a'")
        self.assertEqual(_tools.human_readable_list(['a', 'b']), "'a' or 'b'")
        self.assertEqual(_tools.human_readable_list(['a', 'b', 'c']), "'a', 'b' or 'c'")

    def _test_can_derive_suffix(self, expected_path, path_to_test, suffix_to_test):
        actualPath = _tools.with_suffix(path_to_test, suffix_to_test)
        self.assertEqual(expected_path, actualPath)

    def test_can_build_name_with_suffix(self):
        self._test_can_derive_suffix('hugo.pas', 'hugo.txt', '.pas')
        self._test_can_derive_suffix('hugo', 'hugo.txt', '')
        self._test_can_derive_suffix('hugo.', 'hugo.txt', '.')
        self._test_can_derive_suffix('hugo.txt', 'hugo', '.txt')
        self._test_can_derive_suffix(os.path.join('eggs', 'hugo.pas'), os.path.join('eggs', 'hugo.txt'), '.pas')

    def test_fails_on_mkdirs_with_empty_path(self):
        self.assertRaises(OSError, _tools.mkdirs, '')

    def test_can_compute_length_of_int(self):
        self.assertEqual(3, _tools.length_of_int(123))
        self.assertEqual(1, _tools.length_of_int(0))
        self.assertEqual(1, _tools.length_of_int(9))
        self.assertEqual(2, _tools.length_of_int(-1))
        self.assertEqual(155, _tools.length_of_int(2 ** 512))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
