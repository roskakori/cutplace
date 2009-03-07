"""Cutplace utility functions."""

def camelized(key, firstIsLower=False):
    """Camelized name of possibly multiple words separated by blanks that can be used for variables."""
    assert key is not None
    assert key == key.strip(), "key must be trimmed"
    result = ""
    for part in key.split():
        result += part[0].upper() + part[1:].lower() 
    if firstIsLower and result:
        result = result[0].lower() + result[1:]
    return result
