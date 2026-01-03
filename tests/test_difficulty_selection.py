"""
Tests for AI difficulty selection in LED mode selection.
"""

from pathlib import Path

import matplotlib.pyplot as plt

from chess_game import Square
from led import WS2812BController
from tests.visualization import draw_led_state, setup_led_board_plot

# Create output directory for visualizations
OUTPUT_DIR = Path(__file__).parent / "output" / "leds"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _draw_led_board(
    controller: WS2812BController,
    title: str,
    filename: str,
) -> None:
    """
    Draw the current LED state as a chess board visualization with all 96 LEDs.

    Args:
        controller: LED controller with current state
        title: Plot title
        filename: Output filename
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    setup_led_board_plot(ax, title=title)
    draw_led_state(ax, controller)

    plt.tight_layout()
    output_path = OUTPUT_DIR / filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved visualization: {output_path}")


# Unit tests for difficulty selection


def test_difficulty_not_shown_in_pvp() -> None:
    """Test that difficulty buttons are NOT shown in PvP mode."""
    controller = WS2812BController(use_mock=True)

    # Both a1 and b1 placed = PvP mode
    placed_squares = [Square(0, 0), Square(0, 1)]
    controller.show_mode_selection(placed_squares)

    # Difficulty squares (d1, e1, f1) should be OFF in PvP mode
    assert controller.get_square_color(Square(0, 3)) == (0, 0, 0)  # d1 OFF
    assert controller.get_square_color(Square(0, 4)) == (0, 0, 0)  # e1 OFF
    assert controller.get_square_color(Square(0, 5)) == (0, 0, 0)  # f1 OFF


def test_difficulty_shown_in_ava() -> None:
    """Test that difficulty buttons ARE shown in AI vs AI mode."""
    controller = WS2812BController(use_mock=True)

    # No pieces placed = AI vs AI mode
    placed_squares: list[Square] = []
    controller.show_mode_selection(placed_squares)

    # Difficulty squares should be lit with their default colors
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 0)  # d1 yellow
    assert controller.get_square_color(Square(0, 4)) == (200, 100, 0)  # e1 orange
    assert controller.get_square_color(Square(0, 5)) == (200, 0, 0)  # f1 red


def test_difficulty_shown_in_pva() -> None:
    """Test that difficulty buttons ARE shown in Player vs AI mode."""
    controller = WS2812BController(use_mock=True)

    # Only a1 placed = Player (white) vs AI mode
    placed_squares = [Square(0, 0)]
    controller.show_mode_selection(placed_squares)

    # Difficulty squares should be lit
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 0)  # d1 yellow
    assert controller.get_square_color(Square(0, 4)) == (200, 100, 0)  # e1 orange
    assert controller.get_square_color(Square(0, 5)) == (200, 0, 0)  # f1 red


def test_difficulty_shown_in_avp() -> None:
    """Test that difficulty buttons ARE shown in AI vs Player mode."""
    controller = WS2812BController(use_mock=True)

    # Only b1 placed = AI vs Player (black) mode
    placed_squares = [Square(0, 1)]
    controller.show_mode_selection(placed_squares)

    # Difficulty squares should be lit
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 0)  # d1 yellow
    assert controller.get_square_color(Square(0, 4)) == (200, 100, 0)  # e1 orange
    assert controller.get_square_color(Square(0, 5)) == (200, 0, 0)  # f1 red


def test_difficulty_easy_selected() -> None:
    """Test EASY difficulty selection (d1)."""
    controller = WS2812BController(use_mock=True)

    # AI vs AI mode with d1 selected
    placed_squares = [Square(0, 3)]
    controller.show_mode_selection(placed_squares)

    # d1 should be white (selected), others yellow/orange/red
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 200)  # d1 white
    assert controller.get_square_color(Square(0, 4)) == (200, 100, 0)  # e1 orange
    assert controller.get_square_color(Square(0, 5)) == (200, 0, 0)  # f1 red


def test_difficulty_medium_selected() -> None:
    """Test MEDIUM difficulty selection (e1)."""
    controller = WS2812BController(use_mock=True)

    # AI vs AI mode with e1 selected
    placed_squares = [Square(0, 4)]
    controller.show_mode_selection(placed_squares)

    # e1 should be white (selected), others yellow/red
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 0)  # d1 yellow
    assert controller.get_square_color(Square(0, 4)) == (200, 200, 200)  # e1 white
    assert controller.get_square_color(Square(0, 5)) == (200, 0, 0)  # f1 red


def test_difficulty_hard_selected() -> None:
    """Test HARD difficulty selection (f1)."""
    controller = WS2812BController(use_mock=True)

    # AI vs AI mode with f1 selected
    placed_squares = [Square(0, 5)]
    controller.show_mode_selection(placed_squares)

    # f1 should be white (selected), others yellow/orange
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 0)  # d1 yellow
    assert controller.get_square_color(Square(0, 4)) == (200, 100, 0)  # e1 orange
    assert controller.get_square_color(Square(0, 5)) == (200, 200, 200)  # f1 white


def test_difficulty_priority_when_multiple() -> None:
    """Test that f1 > e1 > d1 priority when multiple difficulties selected."""
    controller = WS2812BController(use_mock=True)

    # Multiple difficulty squares placed (f1 has highest priority)
    placed_squares = [Square(0, 3), Square(0, 4), Square(0, 5)]
    controller.show_mode_selection(placed_squares)

    # Only f1 should be white (highest priority)
    assert controller.get_square_color(Square(0, 3)) == (200, 200, 0)  # d1 yellow
    assert controller.get_square_color(Square(0, 4)) == (200, 100, 0)  # e1 orange
    assert controller.get_square_color(Square(0, 5)) == (200, 200, 200)  # f1 white


# Visualization tests


def test_visualize_ava_no_difficulty() -> None:
    """Visualize AI vs AI mode with no difficulty selected (RANDOM)."""
    controller = WS2812BController(use_mock=True)

    placed_squares: list[Square] = []
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "AI vs AI - No Difficulty (RANDOM)",
        "led_mode_ava_random.png",
    )


def test_visualize_ava_easy() -> None:
    """Visualize AI vs AI mode with EASY difficulty."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 3)]  # d1 selected
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "AI vs AI - EASY Difficulty (d1 selected)",
        "led_mode_ava_easy.png",
    )


def test_visualize_ava_medium() -> None:
    """Visualize AI vs AI mode with MEDIUM difficulty."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 4)]  # e1 selected
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "AI vs AI - MEDIUM Difficulty (e1 selected)",
        "led_mode_ava_medium.png",
    )


def test_visualize_ava_hard() -> None:
    """Visualize AI vs AI mode with HARD difficulty."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 5)]  # f1 selected
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "AI vs AI - HARD Difficulty (f1 selected)",
        "led_mode_ava_hard.png",
    )


def test_visualize_pva_easy() -> None:
    """Visualize Player (white) vs AI mode with EASY difficulty."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 0), Square(0, 3)]  # a1 + d1
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "Player (White) vs AI - EASY Difficulty",
        "led_mode_pva_easy.png",
    )


def test_visualize_avp_medium() -> None:
    """Visualize AI vs Player (black) mode with MEDIUM difficulty."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 1), Square(0, 4)]  # b1 + e1
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "AI vs Player (Black) - MEDIUM Difficulty",
        "led_mode_avp_medium.png",
    )


def test_visualize_pvp_no_difficulty() -> None:
    """Visualize Player vs Player mode (no difficulty buttons shown)."""
    controller = WS2812BController(use_mock=True)

    placed_squares = [Square(0, 0), Square(0, 1)]  # a1 + b1
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "Player vs Player - No AI Difficulty Shown",
        "led_mode_pvp_no_difficulty.png",
    )


def test_visualize_confirm_button() -> None:
    """Visualize all buttons including confirm (h1)."""
    controller = WS2812BController(use_mock=True)

    # AI vs AI with MEDIUM difficulty and h1 confirm selected
    placed_squares = [Square(0, 4), Square(0, 7)]  # e1 + h1
    controller.show_mode_selection(placed_squares)

    _draw_led_board(
        controller,
        "AI vs AI - MEDIUM + Confirm (h1) Selected",
        "led_mode_ava_medium_confirm.png",
    )
