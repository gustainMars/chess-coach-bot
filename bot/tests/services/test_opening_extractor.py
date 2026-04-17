import pytest
from bot.services.opening_extractor import extract_opening_from, _opening_name_from_url


def test_opening_name_from_url_basic():
    assert _opening_name_from_url("https://www.chess.com/openings/Ruy-Lopez-Opening") == "Ruy Lopez Opening"


def test_opening_name_from_url_stops_at_digit():
    assert _opening_name_from_url("https://www.chess.com/openings/Sicilian-Defense-2.Nf3") == "Sicilian Defense"


def test_opening_name_from_url_apostrophe():
    name = _opening_name_from_url("https://www.chess.com/openings/Queens-Gambit-Declined")
    assert "Queen's" in name or "Queens" in name


def test_extract_opening_from_full_pgn():
    pgn = (
        '[Event "Live Chess"]\n'
        '[ECO "C60"]\n'
        '[ECOUrl "https://www.chess.com/openings/Ruy-Lopez-Opening"]\n'
        '\n1. e4 e5 2. Nf3 Nc6 3. Bb5 *'
    )
    result = extract_opening_from(pgn)
    assert result["opening_eco"] == "C60"
    assert "Ruy" in result["opening_name"]


def test_extract_opening_from_missing_eco():
    pgn = '[Event "Live Chess"]\n\n1. e4 e5 *'
    result = extract_opening_from(pgn)
    assert result["opening_eco"] == "?"
    assert result["opening_name"] == "Unknown opening"


def test_extract_opening_from_missing_eco_url():
    pgn = '[Event "Live Chess"]\n[ECO "A00"]\n\n1. a4 *'
    result = extract_opening_from(pgn)
    assert result["opening_eco"] == "A00"
    assert result["opening_name"] == "Unknown opening"


def test_extract_opening_from_empty_string():
    result = extract_opening_from("")
    assert result["opening_eco"] == "?"
    assert result["opening_name"] == "Unknown opening"
