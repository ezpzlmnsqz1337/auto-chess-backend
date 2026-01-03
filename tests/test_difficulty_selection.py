"""
Tests for AI difficulty selection in LED mode selection.
"""

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from chess_game import Square
from led import WS2812BController

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
    import config
    from tests.test_utils import draw_chess_board_grid

    fig, ax = plt.subplots(figsize=(12, 8))

    # Draw board grid using unified function (board coordinate space with capture areas)
    draw_chess_board_grid(ax, show_capture_areas=True, use_motor_coordinates=False)

    # Helper function to draw LED square
    def draw_led_overlay(
        x_pos: float, y_pos: float, led_index: int, color: tuple[int, int, int], chess_label: str | None = None
    ) -> None:
        """Draw LED square with color, LED index, and optional chess notation."""
        # Normalize RGB to 0-1 range
        color_normalized = (color[0] / 255, color[1] / 255, color[2] / 255)
        # Add colored square overlay (slightly transparent to show grid)
        rect = patches.Rectangle(
            (x_pos, y_pos), 1, 1, linewidth=0, facecolor=color_normalized, alpha=0.8, zorder=5
        )
        ax.add_patch(rect)
        
        text_color = "white" if sum(color) < 384 else "black"
        
        if chess_label:
            # Show both chess notation and LED index
            ax.text(
                x_pos + 0.5,
                y_pos + 0.65,
                chess_label,
                ha="center",
                va="center",
                fontsize=8,
                color=text_color,
                weight="bold",
                zorder=6,
            )
            ax.text(
                x_pos + 0.5,
                y_pos + 0.35,
                str(led_index),
                ha="center",
                va="center",
                fontsize=6,
                color=text_color,
                alpha=0.7,
                zorder=6,
            )
        else:
            # Just show LED index for capture areas
            ax.text(
                x_pos + 0.5,
                y_pos + 0.5,
                str(led_index),
                ha="center",
                va="center",
                fontsize=7,
                color=text_color,
                weight="bold",
                zorder=6,
            )

    # Calculate gap for positioning
    gap_in_squares = config.CAPTURE_OFFSET_MM / config.SQUARE_SIZE_MM

    # Draw left capture area LEDs 0-15 (columns -2, -1)
    led_index = 0
    for row in range(config.BOARD_ROWS):
        for col in range(-config.CAPTURE_COLS, 0):
            x_pos = col - gap_in_squares
            color = (0, 0, 0)  # Black/off - no data yet
            draw_led_overlay(x_pos, row, led_index, color)
            led_index += 1

    # Draw main board LEDs 16-79 (columns 0-7)
    led_index = 16
    for row in range(config.BOARD_ROWS):
        for col in range(config.BOARD_COLS):
            square = Square(row, col)
            color = controller.get_square_color(square)
            chess_label = square.to_notation()  # a1, b1, etc.
            draw_led_overlay(col, row, led_index, color, chess_label)
            led_index += 1

    # Draw right capture area LEDs 80-95 (columns 8, 9)
    led_index = 80
    for row in range(config.BOARD_ROWS):
        for col in range(config.BOARD_COLS, config.BOARD_COLS + config.CAPTURE_COLS):
            x_pos = col + gap_in_squares
            color = (0, 0, 0)  # Black/off - no data yet
            draw_led_overlay(x_pos, row, led_index, color)
            led_index += 1

    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=14, weight="bold")
    ax.grid(False)

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
