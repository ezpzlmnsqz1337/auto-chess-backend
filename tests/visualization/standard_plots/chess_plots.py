"""Standardized chess board plotting functions."""

from typing import TYPE_CHECKING

import matplotlib.patheffects as path_effects

from chess_game import ChessGame, PieceType, Player
from tests.visualization.board_drawing import draw_chess_board_grid

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def setup_chess_board_plot(
    ax: "Axes",
    title: str | None = None,
    show_coordinates: bool = True,
) -> None:
    """
    Set up a chess board plot with standard styling for game state visualization.

    Args:
        ax: Matplotlib axes
        title: Optional title for the plot
        show_coordinates: Whether to show a-h and 1-8 labels
    """
    draw_chess_board_grid(ax, show_capture_areas=False, use_motor_coordinates=False)

    if title:
        ax.set_title(title, fontsize=11, fontweight="bold")

    if show_coordinates:
        # Add file labels (a-h) on x-axis
        ax.set_xticks([i + 0.5 for i in range(8)])
        ax.set_xticklabels(["a", "b", "c", "d", "e", "f", "g", "h"])
        # Add rank labels (1-8) on y-axis
        ax.set_yticks([i + 0.5 for i in range(8)])
        ax.set_yticklabels(["1", "2", "3", "4", "5", "6", "7", "8"])
    else:
        ax.set_xticks([])
        ax.set_yticks([])

    ax.set_aspect("equal")


def draw_chess_pieces(ax: "Axes", game: ChessGame) -> None:
    """
    Draw chess pieces on a board with standard styling.

    White pieces are drawn in white with black outline for visibility.
    Black pieces are drawn solid black.

    Args:
        ax: Matplotlib axes (must be set up with chess board already)
        game: Chess game instance containing piece positions
    """
    piece_symbols = {
        PieceType.PAWN: "♟",
        PieceType.KNIGHT: "♞",
        PieceType.BISHOP: "♝",
        PieceType.ROOK: "♜",
        PieceType.QUEEN: "♛",
        PieceType.KING: "♚",
    }

    for square, piece in game.board.items():
        symbol = piece_symbols[piece.piece_type]
        # White pieces with black outline, black pieces solid
        if piece.player == Player.WHITE:
            text = ax.text(
                square.col + 0.5,
                square.row + 0.5,
                symbol,
                fontsize=36,
                ha="center",
                va="center",
                color="white",
                weight="bold",
                zorder=10,
            )
            # Add black outline to white pieces for visibility
            text.set_path_effects(
                [
                    path_effects.Stroke(linewidth=3, foreground="black"),
                    path_effects.Normal(),
                ]
            )
        else:
            ax.text(
                square.col + 0.5,
                square.row + 0.5,
                symbol,
                fontsize=36,
                ha="center",
                va="center",
                color="black",
                weight="bold",
                zorder=10,
            )
