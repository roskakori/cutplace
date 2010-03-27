#!/usr/bin/env python
"""
Cutplace setup for setuptools.
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

# Obtain setuptools if necessary.
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages, Command

# Set up logging early on so import warnings can be logged.
import logging
logging.basicConfig()

from cutplace import dev_reports
from cutplace import ods
from cutplace import tools
from cutplace import version

import os.path
import re
import shutil
import subprocess
import glob

# Various properties that control the build process.
buildFolder = "build"
buildSiteFolder = os.path.join(buildFolder, "site")
docsFolder = "docs"
examplesFolder = "examples"
tutorialFolder = examplesFolder

def _copyFilesToFolder(sourceFolder, targetFolder, pattern=".*"):
    """
    Copy those files in `sourceFolder` to `targetFolder` whose name matches the regex `pattern`.
    
    If the target file already exists, overwrite it.
    
    If an error occurs, no cleanup is performed and a partially copied target file might remain.
    """
    # TODO: Support recursive copy.
    fileNameToCopyRegEx = re.compile(pattern)
    for baseFolder, subFolders, fileNames in os.walk(sourceFolder):
        for fileName in fileNames:
            if fileNameToCopyRegEx.match(fileName) and not ".svn" in baseFolder:
                sourceFilePath = os.path.join(baseFolder, fileName)
                targetFilePath = os.path.join(targetFolder, fileName)
                print "copying %r to %r" % (sourceFilePath, targetFilePath)
                shutil.copy(sourceFilePath, targetFilePath)
            
class _DocsCommand(Command):
    """
    Command for setuptools to build the documentation.
    """
    description = "build documentation"
    user_options = []

    def _convertAllOdsToCsvAndRst(self, folder):
        assert folder is not None
        for baseFolder, subFolders, fileNames in os.walk(folder):
            for fileName in fileNames:
                if os.path.splitext(fileName)[1].lower() == ".ods":
                    self._convertOdsToCsvAndRst(os.path.join(baseFolder, fileName))
                    
    def _convertOdsToCsvAndRst(self, odsSourcePath):
        assert odsSourcePath is not None
        csvTargetPath = tools.withSuffix(odsSourcePath, ".csv")
        rstTargetPath = tools.withSuffix(odsSourcePath, ".rst")
        print "generating %r and %r" % (csvTargetPath, rstTargetPath)
        ods.toCsv(odsSourcePath, csvTargetPath)
        ods.toRst(odsSourcePath, rstTargetPath, firstRowIsHeading=False)

    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        self._convertAllOdsToCsvAndRst("examples")
        # TODO: Remove dead code below.
        # _copyFilesToFolder(tutorialFolder, buildSiteFolder, ".*\\.csv$")
        # _copyFilesToFolder(tutorialFolder, buildSiteFolder, ".*\\.ods$")
        sphinxCall = ["sphinx-build", "-b", "html", "-N", "-q", docsFolder, buildSiteFolder]
        print " ".join(sphinxCall)
        subprocess.check_call(sphinxCall)

class _ReportsCommand(Command):
    """
    Command for setuptools to build the developer reports.
    """
    description = "build developer reports"
    user_options = []

    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        targetFolder = os.path.join("dist", "site", "reports")
        dev_reports.createReports(targetFolder)

setup(
      name="cutplace",
      version=version.VERSION_NUMBER,
      description="validate flat data according to an interface control document",
      author="Thomas Aglassinger",
      author_email="roskakori@users.sourceforge.net",
      url="http://cutplace.sourceforge.net/",
      # TODO: Actually coverage is only required for the development reports. How to express this here?
      install_requires=["coverage", "xlrd"],
      packages=["cutplace"],
      data_files=[
          ("", ["setup.py"]),
          ("", ["license.txt", "README.txt"]),
          ("docs", glob.glob("docs/*.*")),
          ("docs/_static", glob.glob("docs/_static/*.*")),
          ("examples", glob.glob("examples/*.csv") + glob.glob("examples/*.ods"))
      ],
      entry_points={
        "console_scripts": ["cutplace = cutplace.cutplace:mainForScript"]
      },
      license="GNU General Public License 3 or later",
      test_suite="cutplace.test_all.createTestSuite",
      long_description="""Cutplace is a tool to validate that data conform to an interface control document (ICD).

Cutplace works with flat data formats using a separator (such as CSV) or fixed length fields. Such formats are commonly
used to exchange data between different platforms or physically separated systems. Examples are exchanging data
between different partner companies, providing data for data warehousing or other data processing involving
architecturally very different systems like mainframes.

With cutplace you can describe these data in a simple and human readable spreadsheets using popular applications
like Calc or Excel. Unlike a lot of documentation these days, this description does not only describe wishful
thinking. It acts as "executable specification" which cutplace can use to validate that data actually conform to it.""",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Environment :: Web Environment",
          "Intended Audience :: Developers",
          "Intended Audience :: Financial and Insurance Industry",
          "Intended Audience :: Information Technology",
          "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          # TODO: Test with Python 2.4. Who knows, it might actually work.
          "Programming Language :: Python :: 2.5",
          "Programming Language :: Python :: 2.6",
          "Topic :: Documentation",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: Software Development :: Testing"
      ],
      cmdclass={
          "docs": _DocsCommand,
          "reports":_ReportsCommand
      }
)
