from unittest.mock import patch

import chess
import pytest

from bot.services.board_renderer import fen_to_png

STARTING_FEN = chess.STARTING_FEN
BLACK_TO_MOVE_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


@patch("bot.services.board_renderer.cairosvg.svg2png", return_value=b"fakepng")
def test_fen_to_png_returns_bytes(mock_svg2png):
    result = fen_to_png(STARTING_FEN)
    assert isinstance(result, bytes)
    assert result == b"fakepng"


@patch("bot.services.board_renderer.cairosvg.svg2png", return_value=b"fakepng")
@patch("bot.services.board_renderer.chess.svg.board")
def test_white_to_move_not_flipped(mock_board_svg, mock_svg2png):
    mock_board_svg.return_value = "<svg/>"
    fen_to_png(STARTING_FEN)
    _, kwargs = mock_board_svg.call_args
    assert kwargs.get("flipped") is False


@patch("bot.services.board_renderer.cairosvg.svg2png", return_value=b"fakepng")
@patch("bot.services.board_renderer.chess.svg.board")
def test_black_to_move_is_flipped(mock_board_svg, mock_svg2png):
    mock_board_svg.return_value = "<svg/>"
    fen_to_png(BLACK_TO_MOVE_FEN)
    _, kwargs = mock_board_svg.call_args
    assert kwargs.get("flipped") is True


def test_invalid_fen_raises_value_error():
    with pytest.raises(Exception):
        fen_to_png("not-a-valid-fen")


@patch("bot.services.board_renderer.cairosvg.svg2png", return_value=b"png_data")
def test_output_size_is_512(mock_svg2png):
    fen_to_png(STARTING_FEN)
    _, kwargs = mock_svg2png.call_args
    assert kwargs.get("output_width") == 512
    assert kwargs.get("output_height") == 512
