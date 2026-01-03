"""Standardized reed switch board plotting functions."""

from typing import TYPE_CHECKING

from tests.visualization.board_drawing import draw_chess_board_grid
from tests.visualization.standard_plots.chess_plots import draw_chess_pieces

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from chess_game import ChessGame


def setup_reed_switch_plot(
    ax: "Axes",
    title: str | None = None,
) -> None:
    """
    Set up a reed switch board plot for visualizing piece presence.

    Shows main board with proper chess piece rendering, similar to chess board plots.

    Args:
        ax: Matplotlib axes
        title: Optional title for the plot
    """
    draw_chess_board_grid(ax, show_capture_areas=True, use_motor_coordinates=False)

    if title:
        ax.set_title(title, fontsize=11, fontweight="bold")

    # Add file labels (a-h) on x-axis
    ax.set_xticks([i + 0.5 for i in range(8)])
    ax.set_xticklabels(["a", "b", "c", "d", "e", "f", "g", "h"])
    # Add rank labels (1-8) on y-axis
    ax.set_yticks([i + 0.5 for i in range(8)])
    ax.set_yticklabels(["1", "2", "3", "4", "5", "6", "7", "8"])

    ax.set_aspect("equal")


def draw_reed_switch_state(
    ax: "Axes",
    game: "ChessGame | None" = None,
    board_state: list[bool] | None = None,
) -> None:
    """
    Draw reed switch states on a board, showing actual chess pieces.

    Uses real chess piece symbols to show where pieces are detected, with
    white pieces having black outlines for visibility.

    Args:
        ax: Matplotlib axes (must be set up with reed switch board already)
        game: Optional chess game instance with piece positions
        board_state: Optional 64-element list of reed switch states (True = occupied)
                    If board_state is provided, shows simple indicators.
                    If game is provided, shows actual chess pieces.
    """
    # If board_state provided, show piece indicators with generic chess symbol
    if board_state:
        for square_idx in range(64):
            if board_state[square_idx]:
                row = square_idx // 8
                col = square_idx % 8
                # Use a generic chess piece symbol (pawn)
                ax.text(
                    col + 0.5,
                    row + 0.5,
                    "♟",
                    ha="center",
                    va="center",
                    fontsize=36,
                    color="darkgreen",
                    weight="bold",
                    zorder=10,
                )
    elif game:
        # Draw actual chess pieces with correct types
        draw_chess_pieces(ax, game)
