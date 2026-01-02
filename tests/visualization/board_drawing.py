"""Chess board drawing utilities for visualizations."""

from typing import TYPE_CHECKING

import matplotlib.patches as mpatches

import config

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def draw_chess_board_grid(
    ax: "Axes",
    show_capture_areas: bool = True,
    use_motor_coordinates: bool = True,
    square_size: float | None = None,
) -> None:
    """
    Draw chess board grid with alternating shaded squares, and optionally capture areas.

    Unified board drawing function that works in both motor coordinates (mm) and
    board coordinates (0-7 squares).

    Args:
        ax: Matplotlib axes to draw on
        show_capture_areas: If True, draw capture areas on left and right sides
        use_motor_coordinates: If True, use motor coordinate space (mm with offset).
                              If False, use board coordinate space (0-7 squares).
        square_size: Override square size. If None, uses config value for motor coords,
                    or 1.0 for board coords.
    """
    if use_motor_coordinates:
        # Motor coordinate space: positions in mm with motor offset applied
        offset = config.MOTOR_X_OFFSET_MM
        sq_size = square_size or config.SQUARE_SIZE_MM
        main_board_start = offset
    else:
        # Board coordinate space: 0-7 squares, no offset
        offset = 0.0
        sq_size = square_size or 1.0
        main_board_start = 0.0

    if show_capture_areas:
        if use_motor_coordinates:
            left_capture_start = config.LEFT_CAPTURE_START_MM + offset
            right_capture_start = config.RIGHT_CAPTURE_START_MM + offset
        else:
            # In board coordinate space, place captures adjacent (no gap)
            left_capture_start = -config.CAPTURE_COLS * sq_size
            right_capture_start = config.BOARD_COLS * sq_size

        # Draw left capture area (2x8 squares) - Black's captured pieces
        for row in range(config.CAPTURE_ROWS + 1):
            y = row * sq_size
            ax.axhline(y, color="darkred", linewidth=0.5, alpha=0.5)
        for col in range(config.CAPTURE_COLS + 1):
            x = left_capture_start + col * sq_size
            ax.axvline(x, color="darkred", linewidth=0.5, alpha=0.5)

        # Shade left capture squares
        for row in range(config.CAPTURE_ROWS):
            for col in range(config.CAPTURE_COLS):
                x_start = left_capture_start + col * sq_size
                y_start = row * sq_size
                rect = mpatches.Rectangle(
                    (x_start, y_start),
                    sq_size,
                    sq_size,
                    facecolor="lightcoral",
                    alpha=0.2,
                    edgecolor="darkred",
                    linewidth=0.5,
                )
                ax.add_patch(rect)

        # Label left capture area
        ax.text(
            left_capture_start + config.CAPTURE_COLS * sq_size / 2,
            -0.3 * sq_size,
            "Black\nCaptures",
            ha="center",
            va="top",
            fontsize=8,
            color="darkred",
            weight="bold",
        )

        # Draw right capture area (2x8 squares) - White's captured pieces
        for row in range(config.CAPTURE_ROWS + 1):
            y = row * sq_size
            ax.axhline(y, color="darkblue", linewidth=0.5, alpha=0.5)
        for col in range(config.CAPTURE_COLS + 1):
            x = right_capture_start + col * sq_size
            ax.axvline(x, color="darkblue", linewidth=0.5, alpha=0.5)

        # Shade right capture squares
        for row in range(config.CAPTURE_ROWS):
            for col in range(config.CAPTURE_COLS):
                x_start = right_capture_start + col * sq_size
                y_start = row * sq_size
                rect = mpatches.Rectangle(
                    (x_start, y_start),
                    sq_size,
                    sq_size,
                    facecolor="lightblue",
                    alpha=0.2,
                    edgecolor="darkblue",
                    linewidth=0.5,
                )
                ax.add_patch(rect)

        # Label right capture area
        ax.text(
            right_capture_start + config.CAPTURE_COLS * sq_size / 2,
            -0.3 * sq_size,
            "White\nCaptures",
            ha="center",
            va="top",
            fontsize=8,
            color="darkblue",
            weight="bold",
        )

    # Draw main chess board grid lines
    for row in range(config.BOARD_ROWS + 1):
        y = row * sq_size
        ax.axhline(y, color="gray", linewidth=0.5, alpha=0.5)

    for col in range(config.BOARD_COLS + 1):
        x = main_board_start + col * sq_size
        ax.axvline(x, color="gray", linewidth=0.5, alpha=0.5)

    # Shade main board squares like chess board
    for row in range(config.BOARD_ROWS):
        for col in range(config.BOARD_COLS):
            if (row + col) % 2 == 1:
                x_start = main_board_start + col * sq_size
                y_start = row * sq_size
                rect = mpatches.Rectangle(
                    (x_start, y_start),
                    sq_size,
                    sq_size,
                    facecolor="lightgray",
                    alpha=0.3,
                )
                ax.add_patch(rect)


def add_board_coordinates(ax: "Axes", margin: float) -> None:
    """
    Add chess board coordinate labels (a-h, 1-8).

    Args:
        ax: Matplotlib axes to add labels to
        margin: Margin size for label positioning
    """
    # Column labels (a-h)
    for col in range(config.BOARD_COLS):
        x = (col + 0.5) * config.SQUARE_SIZE_MM
        label = chr(ord("a") + col)
        ax.text(x, -margin / 2, label, ha="center", va="center", fontsize=10, fontweight="bold")

    # Row labels (1-8)
    for row in range(config.BOARD_ROWS):
        y = (row + 0.5) * config.SQUARE_SIZE_MM
        ax.text(
            -margin / 2, y, str(row + 1), ha="center", va="center", fontsize=10, fontweight="bold"
        )


def setup_board_axes(ax: "Axes", title: str) -> float:
    """
    Configure axes for chess board visualization.

    Args:
        ax: Matplotlib axes to configure
        title: Title for the plot

    Returns:
        Margin size calculated for the board
    """
    board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
    board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM
    margin = config.SQUARE_SIZE_MM * 0.5

    ax.set_xlabel("X Position (mm)", fontsize=12)
    ax.set_ylabel("Y Position (mm)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_aspect("equal")
    ax.set_xlim(-margin, board_width_mm + margin)
    ax.set_ylim(-margin, board_height_mm + margin)

    return float(margin)
