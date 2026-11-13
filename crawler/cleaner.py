
import re


def clean_text(text):
    """
    Remove unnecessary whitespace and clean webpage text.
    """

    # Replace multiple spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n+", "\n", text)

    # Remove leading and trailing spaces
    text = text.strip()

    return text
