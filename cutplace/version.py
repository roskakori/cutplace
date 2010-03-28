"""
Cutplace version information.
"""
# Copyright (C) 2009-2010 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
VERSION = 0
RELEASE = 6
REVISION = 0

REPOSITORY_ID, VERSION_DATE = "$Id: app.py 123 2010-03-18 12:04:11Z user $".split()[2:4]

VERSION_NUMBER = "%d.%d.%d" % (VERSION, RELEASE, REVISION)
VERSION_TAG = "%s (%s, r%s)" % (VERSION_NUMBER, VERSION_DATE, REPOSITORY_ID)
