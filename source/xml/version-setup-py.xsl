<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" />
<xsl:template match="cutplace-version">#!/usr/bin/env python
"""Cutplace setup for distutils."""

# Obtain setuptools if necessary.
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
      name="cutplace",
      version="<xsl:value-of select="version" />.<xsl:value-of select="release" />.<xsl:value-of select="revision" />",
      description="validate flat data according to an interface control document",
      author="Thomas Aglassinger",
      author_email="roskakori@users.sourceforge.net",
      url="http://cutplace.sourceforge.net/",
      # TODO: Actually coverage is only required for the development reports. How to express this here?
      install_requires = ["coverage", "xlrd"],
      packages = find_packages("source"),
      package_dir={"": "source"},
      # TODO: Include documentation in distribution by copying it to package folder.
      package_data = {"": ["*.html, *.png, *.txt"]},
      entry_points = {
        "console_scripts": ["cutplace = cutplace.cutplace:mainForScript"]
      },
      license = "GNU GPLv3",
      long_description="""Cutplace is a tool to validate that data conform to an interface control document (ICD).

Cutplace works with flat data formats using a separator (such as CSV) or fixed length fields. Such formats are commonly
used to exchange data between different platforms or physically separated systems. Examples are exchanging data
between different partner companies, providing data for data warehousing or other data processing involving
architecturally very different systems like mainframes.

With cutplace you can describe these data in a simple and human readable spreadsheets using popular applications
like Calc or Excel. Unlike a lot of documentation these days, this description does not only describe wishful
thinking. It acts as "executable specification" which cutplace can use to validate that data actually conform to it.""",
      classifiers = [
          "Development Status :: 3 - Alpha",
          "Environment :: Console",
          "Environment :: Web Environment",
          "Intended Audience :: Developers",
          "Intended Audience :: Financial and Insurance Industry",
          "Intended Audience :: Information Technology",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          # TODO: Test with Python 2.4. Who knows, it might actually work.
          "Programming Language :: Python :: 2.5",
          "Programming Language :: Python :: 2.6",
          "Topic :: Documentation",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: Software Development :: Testing"
      ]
)
</xsl:template>
</xsl:stylesheet>
