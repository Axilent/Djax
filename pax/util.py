"""
Utilities.
"""
import unicodedata
import re

def slugify(value):
    """
    Slugs the string.
    """
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return value
