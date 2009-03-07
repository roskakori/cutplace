#!/usr/bin/env python
"""Cutplace setup for distutils."""

from distutils.core import setup

setup(
      name="cutplace",
      # FIXME: Generate version number.
      version="0.0.1",
      description="tool to validate data according to an interface control document",
      author="Thomas Aglassinger",
      author_email="roskakori@users.sourceforge.net",
      package_dir={"": "source"},
      packages=["cutplace"]
      # TODO: url="http://cutplace.sourceforge.net/",
)
