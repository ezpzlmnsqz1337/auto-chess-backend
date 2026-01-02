"""
Tests for WS2812B LED controller with visualizations.
"""

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pytest

from chess_game import ChessGame, Square
from led import WS2812BController

# Create output directory for visualizations
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# LED color constants for testing
class TestLEDColors:
    """Test color constants matching config.TestLEDColors."""

    OFF = (0, 0, 0)
    VALID_MOVE = (0, 100, 0)
    VALID_CAPTURE = (100, 50, 0)
    INVALID_MOVE = (100, 0, 0)
    SELECTED = (0, 50, 100)
    CHECK = (150, 0, 0)
    CHECKMATE = (200, 0, 0)
    STALEMATE = (100, 100, 0)
    LAST_MOVE_FROM = (50, 30, 0)
    LAST_MOVE_TO = (50, 50, 0)
    WHITE_PLAYER = (240, 240, 200)
    BLACK_PLAYER = (180, 180, 220)


def test_initialization() -> None:
    """Test LED controller initialization with mock."""
    controller = WS2812BController(use_mock=True)
    assert controller.use_mock is True
    assert controller.strip is not None


def test_square_to_led_index() -> None:
    """Test square to LED index conversion."""
    controller = WS2812BController(use_mock=True)

    # Test corners
    assert controller.square_to_led_index(Square(0, 0)) == 0  # a1
    assert controller.square_to_led_index(Square(0, 7)) == 7  # h1
    assert controller.square_to_led_index(Square(7, 0)) == 56  # a8
    assert controller.square_to_led_index(Square(7, 7)) == 63  # h8

    # Test middle squares
    assert controller.square_to_led_index(Square(3, 3)) == 27  # d4
    assert controller.square_to_led_index(Square(4, 4)) == 36  # e5


def test_led_index_to_square() -> None:
    """Test LED index to square conversion."""
    controller = WS2812BController(use_mock=True)

    # Test corners
    assert controller.led_index_to_square(0) == Square(0, 0)  # a1
    assert controller.led_index_to_square(7) == Square(0, 7)  # h1
    assert controller.led_index_to_square(56) == Square(7, 0)  # a8
    assert controller.led_index_to_square(63) == Square(7, 7)  # h8

    # Test invalid indices
    with pytest.raises(ValueError):
        controller.led_index_to_square(-1)
    with pytest.raises(ValueError):
        controller.led_index_to_square(64)


def test_round_trip_conversion() -> None:
    """Test that square -> LED index -> square is identity."""
    controller = WS2812BController(use_mock=True)

    for row in range(8):
        for col in range(8):
            square = Square(row, col)
            led_index = controller.square_to_led_index(square)
            back_to_square = controller.led_index_to_square(led_index)
            assert square == back_to_square


def test_set_square_color() -> None:
    """Test setting individual square colors."""
    controller = WS2812BController(use_mock=True)

    # Set a few squares
    controller.set_square_color(Square(0, 0), TestLEDColors.VALID_MOVE)
    controller.set_square_color(Square(3, 3), TestLEDColors.SELECTED)
    controller.set_square_color(Square(7, 7), TestLEDColors.CHECK)

    # Verify colors
    assert controller.get_square_color(Square(0, 0)) == TestLEDColors.VALID_MOVE
    assert controller.get_square_color(Square(3, 3)) == TestLEDColors.SELECTED
    assert controller.get_square_color(Square(7, 7)) == TestLEDColors.CHECK


def test_clear_all() -> None:
    """Test clearing all LEDs."""
    controller = WS2812BController(use_mock=True)

    # Set some colors
    controller.set_square_color(Square(0, 0), TestLEDColors.VALID_MOVE)
    controller.set_square_color(Square(7, 7), TestLEDColors.CHECK)

    # Clear all
    controller.clear_all()

    # Verify all are off
    for row in range(8):
        for col in range(8):
            assert controller.get_square_color(Square(row, col)) == TestLEDColors.OFF


def test_set_all_squares() -> None:
    """Test setting all squares to same color."""
    controller = WS2812BController(use_mock=True)

    # Set all to green
    controller.set_all_squares((0, 100, 0))  # Green

    # Verify all are green
    for row in range(8):
        for col in range(8):
            assert controller.get_square_color(Square(row, col)) == (0, 100, 0)


def test_brightness_control() -> None:
    """Test brightness get/set."""
    controller = WS2812BController(use_mock=True)

    # Test initial brightness
    initial_brightness = controller.get_brightness()
    assert initial_brightness > 0

    # Set new brightness
    controller.set_brightness(128)
    assert controller.get_brightness() == 128

    # Test bounds
    controller.set_brightness(300)  # Over max
    assert controller.get_brightness() == 255

    controller.set_brightness(-10)  # Under min
    assert controller.get_brightness() == 0


def test_highlight_squares() -> None:
    """Test highlighting multiple squares."""
    controller = WS2812BController(use_mock=True)

    squares = [Square(0, 0), Square(0, 1), Square(1, 0), Square(1, 1)]
    controller.highlight_squares(squares, TestLEDColors.VALID_MOVE, clear_first=True)

    # Verify highlighted squares
    for square in squares:
        assert controller.get_square_color(square) == TestLEDColors.VALID_MOVE

    # Verify other squares are off
    assert controller.get_square_color(Square(2, 2)) == TestLEDColors.OFF


def test_show_valid_moves() -> None:
    """Test showing valid moves pattern."""
    controller = WS2812BController(use_mock=True)

    from_square = Square(4, 4)  # e5
    valid_moves = [Square(4, 5), Square(5, 4), Square(3, 4), Square(5, 5)]  # Legal moves
    capture_squares = [Square(5, 5)]  # Capture available

    controller.show_valid_moves(from_square, valid_moves, capture_squares)

    # Verify selected square is blue
    assert controller.get_square_color(from_square) == TestLEDColors.SELECTED

    # Verify valid moves are green (except captures)
    for move in valid_moves:
        if move in capture_squares:
            assert controller.get_square_color(move) == TestLEDColors.VALID_CAPTURE
        else:
            assert controller.get_square_color(move) == TestLEDColors.VALID_MOVE


def test_show_check_state() -> None:
    """Test showing check indicator."""
    controller = WS2812BController(use_mock=True)

    king_square = Square(4, 4)
    controller.show_check_state(king_square)

    assert controller.get_square_color(king_square) == TestLEDColors.CHECK


def test_show_invalid_move_feedback() -> None:
    """Test showing invalid move feedback."""
    controller = WS2812BController(use_mock=True)

    from_square = Square(0, 0)
    to_square = Square(7, 7)

    controller.show_invalid_move_feedback(from_square, to_square)

    assert controller.get_square_color(from_square) == TestLEDColors.INVALID_MOVE
    assert controller.get_square_color(to_square) == TestLEDColors.INVALID_MOVE


def test_show_move_feedback() -> None:
    """Test showing last move feedback."""
    controller = WS2812BController(use_mock=True)

    from_square = Square(1, 4)  # e2
    to_square = Square(3, 4)  # e4

    controller.show_move_feedback(from_square, to_square)

    assert controller.get_square_color(from_square) == TestLEDColors.LAST_MOVE_FROM
    assert controller.get_square_color(to_square) == TestLEDColors.LAST_MOVE_TO


def test_show_checkmate() -> None:
    """Test showing checkmate indicator."""
    controller = WS2812BController(use_mock=True)

    king_square = Square(7, 4)
    controller.show_checkmate(king_square)

    assert controller.get_square_color(king_square) == TestLEDColors.CHECKMATE


def test_show_stalemate() -> None:
    """Test showing stalemate pattern."""
    controller = WS2812BController(use_mock=True)

    controller.show_stalemate()

    # Verify center squares are yellow
    center_squares = [Square(3, 3), Square(3, 4), Square(4, 3), Square(4, 4)]
    for square in center_squares:
        assert controller.get_square_color(square) == TestLEDColors.STALEMATE


def test_show_player_turn() -> None:
    """Test showing player turn indicator."""
    controller = WS2812BController(use_mock=True)
    game = ChessGame()

    # Test white's turn (initial position)
    controller.show_player_turn(game)
    # White's pieces should be lit (e.g., a1 has white rook)
    assert controller.get_square_color(Square(0, 0)) == TestLEDColors.WHITE_PLAYER
    # Black's pieces should be off (e.g., a8 has black rook)
    assert controller.get_square_color(Square(7, 0)) == TestLEDColors.OFF

    # Make a move to switch to black's turn
    game.make_move(Square(1, 4), Square(3, 4))  # e2 to e4
    controller.show_player_turn(game)
    # Black's pieces should be lit (e.g., a8 has black rook)
    assert controller.get_square_color(Square(7, 0)) == TestLEDColors.BLACK_PLAYER
    # White's pieces should be off (e.g., a1 has white rook)
    assert controller.get_square_color(Square(0, 0)) == TestLEDColors.OFF


def test_rainbow_pattern() -> None:
    """Test rainbow pattern generation."""
    controller = WS2812BController(use_mock=True)

    controller.rainbow_pattern(brightness_scale=0.5)

    # Verify all squares have different colors (rainbow effect)
    colors = set()
    for row in range(8):
        for col in range(8):
            colors.add(controller.get_square_color(Square(row, col)))

    # Should have many unique colors (at least 32 different hues)
    assert len(colors) >= 32


def test_cleanup() -> None:
    """Test cleanup turns off all LEDs."""
    controller = WS2812BController(use_mock=True)

    # Set some colors
    controller.set_all_squares(TestLEDColors.CHECK)

    # Cleanup
    controller.cleanup()

    # Verify all are off
    for row in range(8):
        for col in range(8):
            assert controller.get_square_color(Square(row, col)) == TestLEDColors.OFF


# Visualization tests


def _draw_led_board(
    controller: WS2812BController,
    title: str,
    filename: str,
) -> None:
    """
    Draw the current LED state as a chess board visualization.

    Args:
        controller: LED controller with current state
        title: Plot title
        filename: Output filename
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    # Draw board squares
    for row in range(8):
        for col in range(8):
            square = Square(row, col)
            color = controller.get_square_color(square)

            # Normalize RGB to 0-1 for matplotlib
            rgb_normalized = (color[0] / 255, color[1] / 255, color[2] / 255)

            # Add square
            rect = patches.Rectangle(
                (col, row), 1, 1, linewidth=1, edgecolor="gray", facecolor=rgb_normalized
            )
            ax.add_patch(rect)

            # Add square label
            label = square.to_notation()
            ax.text(
                col + 0.5,
                row + 0.5,
                label,
                ha="center",
                va="center",
                fontsize=8,
                color="white" if sum(color) < 384 else "black",
            )

    # Set board properties
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_aspect("equal")
    ax.set_xticks(range(9))
    ax.set_yticks(range(9))
    ax.set_xticklabels(["", "a", "b", "c", "d", "e", "f", "g", "h"])
    ax.set_yticklabels(["", "1", "2", "3", "4", "5", "6", "7", "8"])
    ax.set_title(title, fontsize=14, pad=10)
    ax.grid(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=100)
    plt.close()


def test_visualize_valid_moves() -> None:
    """Visualize valid moves pattern for knight on e4."""
    controller = WS2812BController(use_mock=True)

    from_square = Square(3, 4)  # e4
    # Knight moves from e4
    valid_moves = [
        Square(5, 5),  # g6
        Square(5, 3),  # d6
        Square(4, 6),  # g5
        Square(4, 2),  # c5
        Square(2, 6),  # g3
        Square(2, 2),  # c3
        Square(1, 5),  # f2
        Square(1, 3),  # d2
    ]

    controller.show_valid_moves(from_square, valid_moves)

    _draw_led_board(
        controller,
        "LED Pattern: Valid Knight Moves from e4",
        "led_knight_moves.png",
    )


def test_visualize_check_pattern() -> None:
    """Visualize check indicator."""
    controller = WS2812BController(use_mock=True)

    king_square = Square(4, 4)  # e5
    controller.show_check_state(king_square)

    _draw_led_board(
        controller,
        "LED Pattern: Check Indicator",
        "led_check_indicator.png",
    )


def test_visualize_invalid_move() -> None:
    """Visualize invalid move feedback."""
    controller = WS2812BController(use_mock=True)

    from_square = Square(1, 4)  # e2
    to_square = Square(5, 4)  # e6 (invalid for pawn)

    controller.show_invalid_move_feedback(from_square, to_square)

    _draw_led_board(
        controller,
        "LED Pattern: Invalid Move Feedback",
        "led_invalid_move.png",
    )


def test_visualize_rainbow_pattern() -> None:
    """Visualize rainbow pattern."""
    controller = WS2812BController(use_mock=True)

    controller.rainbow_pattern(brightness_scale=1.0)

    _draw_led_board(
        controller,
        "LED Pattern: Rainbow Effect",
        "led_rainbow.png",
    )


def test_visualize_player_turn() -> None:
    """Visualize player turn indicator."""
    controller = WS2812BController(use_mock=True)
    game = ChessGame()

    controller.show_player_turn(game)

    _draw_led_board(
        controller,
        "LED Pattern: White's Turn (White Pieces Highlighted)",
        "led_white_turn.png",
    )


def test_visualize_stalemate() -> None:
    """Visualize stalemate pattern."""
    controller = WS2812BController(use_mock=True)

    controller.show_stalemate()

    _draw_led_board(
        controller,
        "LED Pattern: Stalemate",
        "led_stalemate.png",
    )
