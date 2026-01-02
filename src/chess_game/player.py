"""Player enumeration for chess game."""

from enum import Enum


class Player(Enum):
    """Chess players."""

    WHITE = "white"
    BLACK = "black"

    def opposite(self) -> "Player":
        """Return the opposite player."""
        return Player.BLACK if self == Player.WHITE else Player.WHITE
