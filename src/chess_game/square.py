"""Square representation for chess board."""

from dataclasses import dataclass


@dataclass
class Square:
    """A chess board square identified by row and column (0-7)."""

    row: int  # 0 = rank 1 (white's side), 7 = rank 8 (black's side)
    col: int  # 0 = a-file, 7 = h-file

    def __post_init__(self) -> None:
        """Validate square coordinates."""
        if not (0 <= self.row < 8 and 0 <= self.col < 8):
            raise ValueError(f"Invalid square coordinates: ({self.row}, {self.col})")

    def to_notation(self) -> str:
        """Convert to algebraic notation (e.g., 'e4')."""
        file = chr(ord("a") + self.col)
        rank = str(self.row + 1)
        return f"{file}{rank}"

    @staticmethod
    def from_notation(notation: str) -> "Square":
        """Create square from algebraic notation (e.g., 'e4')."""
        if len(notation) != 2:
            raise ValueError(f"Invalid notation: {notation}")
        col = ord(notation[0].lower()) - ord("a")
        row = int(notation[1]) - 1
        return Square(row, col)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Square):
            return NotImplemented
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        """Make square hashable."""
        return hash((self.row, self.col))
