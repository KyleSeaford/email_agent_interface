"""
Text utility functions for cleaning and normalizing text data.
Provides functions to handle control characters, newlines, and Unicode normalization.
"""

# Standard library imports
import unicodedata

# Create a translation table that maps control characters to None
CONTROL_CHARS = "".join(chr(i) for i in range(32) if i not in [9, 10, 13]) + chr(127)
CONTROL_CHAR_TABLE = str.maketrans("", "", CONTROL_CHARS)

def clean_text(text):
    """Clean text to ensure it can be properly serialized"""
    if not isinstance(text, str):
        return text

    # Remove control characters except tabs
    cleaned = text.translate(CONTROL_CHAR_TABLE)

    # Replace newlines and carriage returns with spaces
    cleaned = cleaned.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    # Replace multiple spaces with a single space
    cleaned = ' '.join(cleaned.split())

    # Normalize Unicode
    cleaned = unicodedata.normalize("NFC", cleaned)
    return cleaned
