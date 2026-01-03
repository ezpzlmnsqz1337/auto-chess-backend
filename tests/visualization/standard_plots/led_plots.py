"""Standardized LED board plotting functions."""

from typing import TYPE_CHECKING, Any

import matplotlib.patches as patches

import config
from chess_game import Square
from tests.visualization.board_drawing import draw_chess_board_grid

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def setup_led_board_plot(
    ax: "Axes",
    title: str | None = None,
) -> None:
    """
    Set up an LED board plot for visualizing LED states across all 96 LEDs.

    Shows main board (64) and capture areas (32) with proper spacing.

    Args:
        ax: Matplotlib axes
        title: Optional title for the plot
    """
    draw_chess_board_grid(ax, show_capture_areas=True, use_motor_coordinates=False)

    if title:
        ax.set_title(title, fontsize=11, fontweight="bold")

    ax.set_aspect("equal")


def draw_led_state(
    ax: "Axes",
    led_controller: Any,
) -> None:
    """
    Draw LED states on a board with color overlays and labels.

    Shows all 96 LEDs with their current colors, displaying both chess notation
    (for main board) and LED indices.

    Args:
        ax: Matplotlib axes (must be set up with LED board already)
        led_controller: LED controller instance with current state
    """
    # Calculate gap for positioning
    gap_in_squares = config.CAPTURE_OFFSET_MM / config.SQUARE_SIZE_MM

    # Helper function to draw LED square
    def draw_led_overlay(
        x_pos: float,
        y_pos: float,
        led_index: int,
        color: tuple[int, int, int],
        chess_label: str | None = None,
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
                fontsize=8,
                color=text_color,
                weight="bold",
                zorder=6,
            )

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
            square_led = Square(row, col)
            color = led_controller.get_square_color(square_led)
            chess_label = square_led.to_notation()  # a1, b1, etc.
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
