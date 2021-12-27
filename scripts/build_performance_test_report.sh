#!/bin/sh
# Update requirements files and pre-commit hooks to current versions.
set -e
echo "🏃 Running performance test"
OUTPUT_FILE="performance.xml"
poetry run pytest --junit-xml $OUTPUT_FILE tests/test_performance.py
echo "🎉 Successfully stored performance test report in $OUTPUT_FILE"
