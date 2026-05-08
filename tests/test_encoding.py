"""
Tests for fixing Facebook's double-encoded UTF-8 mojibake.
"""

from fb_network_scorer.parser import fix_facebook_encoding


def test_fix_facebook_encoding_vietnamese():
    # Facebook encodes "Hoàng" as "Ho\u00c3\u00a0ng" in JSON, which loads into Python as "HoÃ\xa0ng"
    # This simulates what json.load() gives us for double-encoded text
    mojibake = "Ho\u00c3\u00a0ng"
    fixed = fix_facebook_encoding(mojibake)
    assert fixed == "Hoàng"

def test_fix_facebook_encoding_ascii():
    assert fix_facebook_encoding("Alice") == "Alice"

def test_fix_facebook_encoding_empty():
    assert fix_facebook_encoding("") == ""
    assert fix_facebook_encoding(None) is None

def test_fix_facebook_encoding_invalid():
    # If the text is already correctly decoded or has characters outside latin-1,
    # the function should gracefully fall back to returning the original string.
    already_correct = "Lữ Hữu"
    assert fix_facebook_encoding(already_correct) == already_correct
