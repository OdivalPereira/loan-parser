import pytest

from backend.parsers import ParserNotFoundError, parse


def test_parse_unknown_parser():
    with pytest.raises(ParserNotFoundError):
        parse("inexistent", b"")

