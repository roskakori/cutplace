#!/bin/sh
# Update requirements files and pre-commit hooks to current versions.
set -e
poetry update
pre-commit autoupdate
