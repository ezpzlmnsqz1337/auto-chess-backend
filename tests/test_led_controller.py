"""
Tests for WS2812B LED controller with visualizations.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from chess_game import ChessGame, Square
from led import WS2812BController
from tests.visualization import draw_led_state, setup_led_board_plot

# Create output directory for visualizations
OUTPUT_DIR = Path(__file__).parent / "output" / "leds"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    """Draw the current LED state using standardized plotting functions.

    Args:
        controller: LED controller with current state
        title: Plot title
        filename: Output filename
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    # Use standardized LED board plotting
    setup_led_board_plot(ax, title=title)
    draw_led_state(ax, controller)

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


def test_mode_selection_no_pieces() -> None:
    """Test mode selection with no pieces placed (AvA mode)."""
    controller = WS2812BController(use_mock=True)

    placed_squares: list[Square] = []
    controller.show_mode_selection(placed_squares)

    # Verify button colors
    a1_idx = controller.square_to_led_index(Square(0, 0))
    b1_idx = controller.square_to_led_index(Square(0, 1))
    h1_idx = controller.square_to_led_index(Square(0, 7))

    assert controller.strip.pixels[a1_idx] == (0, 150, 200), "a1 should be light blue"
    assert controller.strip.pixels[b1_idx] == (0, 0, 200), "b1 should be blue"
    assert controller.strip.pixels[h1_idx] == (0, 200, 0), "h1 should be green"

    # Verify some text squares are white (AvA text should be displayed)
    # At least some squares should be lit with white text
    white_count = sum(1 for i in range(64) if controller.strip.pixels[i] == (200, 200, 200))
    assert white_count > 0, "Should have white text squares for AvA"


def test_mode_selection_one_piece() -> None:
    """Test mode selection with a1 placed (PvA mode, player white)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 0)]  # a1 placed
    controller.show_mode_selection(placed_squares)

    # Verify button colors
    a1_idx = controller.square_to_led_index(Square(0, 0))
    b1_idx = controller.square_to_led_index(Square(0, 1))
    h1_idx = controller.square_to_led_index(Square(0, 7))

    assert controller.strip.pixels[a1_idx] == (200, 200, 200), "a1 should be white (selected)"
    assert controller.strip.pixels[b1_idx] == (0, 0, 200), "b1 should be blue"
    assert controller.strip.pixels[h1_idx] == (0, 200, 0), "h1 should be green"

    # Verify some text squares are white (PvA text should be displayed)
    white_count = sum(1 for i in range(64) if controller.strip.pixels[i] == (200, 200, 200))
    assert white_count > 0, "Should have white text squares for PvA"


def test_mode_selection_one_piece_b1() -> None:
    """Test mode selection with b1 placed (PvA mode, player black)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 1)]  # b1 placed
    controller.show_mode_selection(placed_squares)

    # Verify button colors
    a1_idx = controller.square_to_led_index(Square(0, 0))
    b1_idx = controller.square_to_led_index(Square(0, 1))
    h1_idx = controller.square_to_led_index(Square(0, 7))

    assert controller.strip.pixels[a1_idx] == (0, 150, 200), "a1 should be light blue"
    assert controller.strip.pixels[b1_idx] == (200, 200, 200), "b1 should be white (selected)"
    assert controller.strip.pixels[h1_idx] == (0, 200, 0), "h1 should be green"

    # Verify some text squares are white (PvA text should be displayed)
    white_count = sum(1 for i in range(64) if controller.strip.pixels[i] == (200, 200, 200))
    assert white_count > 0, "Should have white text squares for PvA"


def test_mode_selection_two_pieces() -> None:
    """Test mode selection with a1 and b1 placed (PvP mode)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 0), Square(0, 1)]  # a1 and b1 placed
    controller.show_mode_selection(placed_squares)

    # Verify button colors
    a1_idx = controller.square_to_led_index(Square(0, 0))
    b1_idx = controller.square_to_led_index(Square(0, 1))
    h1_idx = controller.square_to_led_index(Square(0, 7))

    assert controller.strip.pixels[a1_idx] == (200, 200, 200), "a1 should be white (selected)"
    assert controller.strip.pixels[b1_idx] == (200, 200, 200), "b1 should be white (selected)"
    assert controller.strip.pixels[h1_idx] == (0, 200, 0), "h1 should be green"

    # Verify some text squares are white (PvP text should be displayed)
    white_count = sum(1 for i in range(64) if controller.strip.pixels[i] == (200, 200, 200))
    assert white_count > 0, "Should have white text squares for PvP"


def test_waiting_for_pieces() -> None:
    """Test waiting for pieces to be placed."""
    controller = WS2812BController(use_mock=True)

    # Define starting position squares
    correct_squares = [
        # White pieces (rows 0-1)
        Square(0, 0),
        Square(0, 1),
        Square(0, 2),
        Square(1, 0),
        Square(1, 1),
        # Black pieces (rows 6-7)
        Square(6, 0),
        Square(6, 1),
        Square(7, 0),
        Square(7, 1),
        Square(7, 2),
    ]

    # Some pieces already placed
    placed_squares = [
        Square(0, 0),  # Correctly placed
        Square(1, 0),  # Correctly placed
        Square(7, 0),  # Correctly placed
    ]

    controller.show_waiting_for_pieces(placed_squares, correct_squares)

    # Verify placed pieces are green
    for square in placed_squares:
        led_idx = controller.square_to_led_index(square)
        color = controller.strip.pixels[led_idx]
        assert color == (0, 200, 0), f"Expected green at placed {square}"

    # Verify missing pieces show RED indicators
    missing = [sq for sq in correct_squares if sq not in placed_squares]
    for square in missing:
        led_idx = controller.square_to_led_index(square)
        color = controller.strip.pixels[led_idx]
        assert color == (200, 0, 0), f"Expected RED indicator at {square}"


def test_piece_placed_feedback() -> None:
    """Test piece placement feedback (correct vs incorrect)."""
    controller = WS2812BController(use_mock=True)

    # Test correct placement
    square = Square(0, 0)
    controller.show_piece_placed_feedback(square, is_correct=True)
    led_idx = controller.square_to_led_index(square)
    assert controller.strip.pixels[led_idx] == (0, 200, 0)  # Bright green

    # Test incorrect placement
    controller.clear_all()
    square = Square(3, 3)
    controller.show_piece_placed_feedback(square, is_correct=False)
    led_idx = controller.square_to_led_index(square)
    assert controller.strip.pixels[led_idx] == (200, 0, 0)  # Red


def test_visualize_mode_selection_no_pieces() -> None:
    """Visualize mode selection with no pieces (AvA)."""
    controller = WS2812BController(use_mock=True)

    placed_squares: list[Square] = []
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "Mode Selection: No Pieces (a1=Blue, b1=Light Blue, h1=Green, Text=AvA)",
        "led_mode_no_pieces.png",
    )


def test_visualize_mode_selection_one_piece() -> None:
    """Visualize mode selection with a1 placed (PvA, player white)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 0)]  # a1 placed
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "Mode Selection: a1 Placed (Player vs AI - Player White)",
        "led_mode_one_piece_a1.png",
    )


def test_visualize_mode_selection_one_piece_b1() -> None:
    """Visualize mode selection with b1 placed (PvA, player black)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 1)]  # b1 placed
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "Mode Selection: b1 Placed (Player vs AI - Player Black)",
        "led_mode_one_piece_b1.png",
    )


def test_visualize_mode_selection_two_pieces() -> None:
    """Visualize mode selection with a1,b1 placed (PvP)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 0), Square(0, 1)]  # a1 and b1 placed
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "Mode Selection: a1,b1 Placed (Player vs Player)",
        "led_mode_two_pieces.png",
    )


def test_visualize_waiting_for_pieces_empty() -> None:
    """Visualize board waiting for all pieces to be placed."""
    controller = WS2812BController(use_mock=True)

    # All starting position squares
    correct_squares = []
    # White pieces (rows 0-1)
    for col in range(8):
        correct_squares.append(Square(0, col))  # Back rank
        correct_squares.append(Square(1, col))  # Pawns
    # Black pieces (rows 6-7)
    for col in range(8):
        correct_squares.append(Square(6, col))  # Pawns
        correct_squares.append(Square(7, col))  # Back rank

    placed_squares: list[Square] = []  # No pieces placed yet

    controller.show_waiting_for_pieces(placed_squares, correct_squares)

    _draw_led_board(
        controller,
        "Waiting for Pieces: Empty Board (RED=Need Piece)",
        "led_waiting_empty.png",
    )


def test_visualize_waiting_for_pieces_partial() -> None:
    """Visualize board with some pieces placed correctly."""
    controller = WS2812BController(use_mock=True)

    # All starting position squares
    correct_squares = []
    for col in range(8):
        correct_squares.append(Square(0, col))  # White back rank
        correct_squares.append(Square(1, col))  # White pawns
        correct_squares.append(Square(6, col))  # Black pawns
        correct_squares.append(Square(7, col))  # Black back rank

    # Half of pieces placed
    placed_squares = [
        # White back rank placed
        Square(0, 0),
        Square(0, 1),
        Square(0, 2),
        Square(0, 3),
        Square(0, 4),
        Square(0, 5),
        Square(0, 6),
        Square(0, 7),
        # Some white pawns
        Square(1, 0),
        Square(1, 1),
        Square(1, 2),
        # Some black pieces
        Square(7, 0),
        Square(7, 7),
        Square(6, 3),
        Square(6, 4),
    ]

    controller.show_waiting_for_pieces(placed_squares, correct_squares)

    _draw_led_board(
        controller,
        "Waiting for Pieces: Partial Setup (GREEN=Placed, RED=Still Needed)",
        "led_waiting_partial.png",
    )


def test_visualize_waiting_for_pieces_complete() -> None:
    """Visualize board with all pieces correctly placed."""
    controller = WS2812BController(use_mock=True)

    # All starting position squares
    correct_squares = []
    for col in range(8):
        correct_squares.append(Square(0, col))
        correct_squares.append(Square(1, col))
        correct_squares.append(Square(6, col))
        correct_squares.append(Square(7, col))

    # All pieces placed
    placed_squares = correct_squares.copy()

    controller.show_waiting_for_pieces(placed_squares, correct_squares)

    _draw_led_board(
        controller,
        "Waiting for Pieces: Complete Setup (All Green - Ready to Play!)",
        "led_waiting_complete.png",
    )


def test_visualize_piece_placed_correct() -> None:
    """Visualize feedback when piece placed correctly."""
    controller = WS2812BController(use_mock=True)

    # Show a piece being placed correctly on a1
    square = Square(0, 0)
    controller.show_piece_placed_feedback(square, is_correct=True)

    _draw_led_board(
        controller,
        "Piece Placement Feedback: Correct (Bright Green Flash)",
        "led_piece_placed_correct.png",
    )


def test_visualize_piece_placed_incorrect() -> None:
    """Visualize feedback when piece placed incorrectly."""
    controller = WS2812BController(use_mock=True)

    # Show a piece being placed incorrectly on d4
    square = Square(3, 3)
    controller.show_piece_placed_feedback(square, is_correct=False)

    _draw_led_board(
        controller,
        "Piece Placement Feedback: Incorrect (Red Flash)",
        "led_piece_placed_incorrect.png",
    )
