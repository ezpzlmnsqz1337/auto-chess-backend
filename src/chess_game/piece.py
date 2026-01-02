"""Piece types and piece class for chess game."""

from dataclasses import dataclass
from enum import Enum

from chess_game.player import Player


class PieceType(Enum):
    """Types of chess pieces."""

    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "B"
    ROOK = "R"
    QUEEN = "Q"
    KING = "K"


@dataclass
class Piece:
    """A chess piece with type and color."""

    piece_type: PieceType
    player: Player
    has_moved: bool = False  # Track if piece has moved (for castling, pawn double-move)

    def __str__(self) -> str:
        """String representation: uppercase for white, lowercase for black."""
        symbol = self.piece_type.value
        return symbol if self.player == Player.WHITE else symbol.lower()
