"""
Test for `_tools` module.
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

import os.path
import unittest

from cutplace import _tools
from . import dev_test


class ToolsTest(unittest.TestCase):
    def test_can_create_test_date_time(self):
        for _ in range(15):
            dateTime = dev_test.random_datetime()
            self.assertTrue(dateTime is not None)
            self.assertNotEqual(dateTime, "")

    def test_can_create_test_name(self):
        for _ in range(15):
            name = dev_test.random_name()
            self.assertTrue(name is not None)
            self.assertNotEqual(name, "")

    def test_can_create_test_customer_row(self):
        for customer_id in range(15):
            row = dev_test.create_test_customer_row(customer_id)
            self.assertTrue(row is not None)
            self.assertEqual(len(row), 6)

    def test_can_query_version(self):
        # Simply exercise these functions, their results do not really matter.
        _tools.platformVersion()
        _tools.pythonVersion()

    def test_can_validate_python_name(self):
        self.assertEqual(_tools.validatedPythonName("x", "abc_123"), "abc_123")
        self.assertEqual(_tools.validatedPythonName("x", " abc_123 "), "abc_123")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "1337")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", " ")
        self.assertRaises(NameError, _tools.validatedPythonName, "x", "a.b")

    def test_can_build_human_readable_list(self):
        self.assertEqual(_tools.humanReadableList([]), "")
        self.assertEqual(_tools.humanReadableList(["a"]), "'a'")
        self.assertEqual(_tools.humanReadableList(["a", "b"]), "'a' or 'b'")
        self.assertEqual(_tools.humanReadableList(["a", "b", "c"]), "'a', 'b' or 'c'")

    def _test_can_derive_suffix(self, expectedPath, pathToTest, suffixToTest):
        actualPath = _tools.withSuffix(pathToTest, suffixToTest)
        self.assertEqual(expectedPath, actualPath)

    def test_can_build_name_with_suffix(self):
        self._test_can_derive_suffix("hugo.pas", "hugo.txt", ".pas")
        self._test_can_derive_suffix("hugo", "hugo.txt", "")
        self._test_can_derive_suffix("hugo.", "hugo.txt", ".")
        self._test_can_derive_suffix("hugo.txt", "hugo", ".txt")
        self._test_can_derive_suffix(os.path.join("eggs", "hugo.pas"), os.path.join("eggs", "hugo.txt"), ".pas")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
