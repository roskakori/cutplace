<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" />
<xsl:template match="cutplace-version">#!/usr/bin/env python
"""Cutplace setup for distutils."""

from distutils.core import setup

setup(
      name="cutplace",
      version="<xsl:value-of select="version" />.<xsl:value-of select="release" />.<xsl:value-of select="revision" />",
      description="tool to validate data according to an interface control document",
      author="Thomas Aglassinger",
      author_email="roskakori@users.sourceforge.net",
      package_dir={"": "source"},
      packages=["cutplace"],
      license = "GNU GPLv3",
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
      # TODO: url="http://cutplace.sourceforge.net/",
)
</xsl:template>
</xsl:stylesheet>
