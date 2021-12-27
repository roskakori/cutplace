#!/bin/sh
set -e
poetry run pytest --cov=cutplace --cov-branch --cov-report=xml --junitxml=test-report.xml
