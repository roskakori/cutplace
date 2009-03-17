<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" />
<xsl:template match="cutplace-version">#!/usr/bin/env python
"""Cutplace setup for distutils."""

from distutils.core import setup

setup(
      name="cutplace",
      version="<xsl:value-of select="version" />.<xsl:value-of select="release" />.<xsl:value-of select="revision" />",
      description="validate flat data according to an interface control document",
      author="Thomas Aglassinger",
      author_email="roskakori@users.sourceforge.net",
      url="http://cutplace.sourceforge.net/",
      package_dir={"": "source"},
      packages=["cutplace"],
      scripts=["source/scripts/cutplace"],
      license = "GNU GPLv3",
      long_description=""""Cutplace is a tool to validate that data conform to an interface control document (IDC).

Cutplace works with flat data formats using a separator (such as CSV) or a fixed format. Such formats are commonly
used to exchange data between different platforms or physically separated systems. Examples are exchanging data
between different partner companies, providing data for data warehousing or other data processing involving
architecturally very different systems like mainframes.

With cutplace you can describe these data in a simple and human readable spreadsheets using popular applications
like Calc or Excel. Unlike a lot of documentation these days, this description does not only describe wishful
thinking. It acts as "executable specification" that cutplace can use to validate that data actually conform to it.""",
      classifiers = [
          "Development Status :: 3 - Alpha",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: Financial and Insurance Industry",
          "Intended Audience :: Healthcare Industry",
          "Intended Audience :: Information Technology",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 2.5", # TODO: Test with other Python versions
          "Topic :: Documentation",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: Software Development :: Testing"
      ]
)
</xsl:template>
</xsl:stylesheet>
