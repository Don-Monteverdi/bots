
from . import erste, otp

PARSERS = [erste, otp]

def detect_and_parse(text):
    for parser in PARSERS:
        if parser.detect(text):
            return parser.parse(text)
    raise ValueError("Unknown bank format: no parser matched.")
