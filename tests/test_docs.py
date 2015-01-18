"""
Tests for data formats.
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
import doctest
import os.path
import unittest


def _path_to_docs_file(file_name):
    docs_folder = os.path.join(os.path.pardir, 'docs')
    return os.path.join(docs_folder, file_name)


class DocumentationTest(unittest.TestCase):
    def test_can_run_examples_in_api_rst(self):
        doctest.testfile(_path_to_docs_file('api.rst'))


if __name__ == '__main__':
    unittest.main()
