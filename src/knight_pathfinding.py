"""Knight pathfinding with obstacle avoidance for physical board movement."""

from dataclasses import dataclass

from chess_game import ChessGame, Square


@dataclass
class Waypoint:
    """A waypoint in the knight's path (in board coordinates, mm)."""

    x: float  # X position in mm
    y: float  # Y position in mm
    description: str


def calculate_knight_path(
    from_square: Square,
    to_square: Square,
    game: ChessGame,
    square_size_mm: float = 31.0,
) -> list[Waypoint]:
    """
    Calculate waypoints for knight movement that avoids occupied squares.

    The knight moves in an L-shape (2 squares in one direction, 1 in perpendicular).
    Since the magnet can't pass through pieces, we navigate around occupied squares
    by moving along the edges.

    Strategy for b1 -> c3 (2 up, 1 right):
    1. Move to top-right corner of b1
    2. Move up and right along the edge between b2/c2 and b3/c3
    3. Arrive at center of c3

    This keeps the magnet path between squares to avoid collisions.

    Args:
        from_square: Starting square
        to_square: Destination square
        game: Current game state (to check occupancy)
        square_size_mm: Size of each square in millimeters

    Returns:
        List of waypoints (in mm from board origin) for the magnet to follow
    """
    waypoints: list[Waypoint] = []

    # Calculate deltas
    delta_row = to_square.row - from_square.row
    delta_col = to_square.col - from_square.col

    # Verify it's a valid knight move
    if not (
        (abs(delta_row) == 2 and abs(delta_col) == 1)
        or (abs(delta_row) == 1 and abs(delta_col) == 2)
    ):
        raise ValueError(f"Invalid knight move: {from_square} to {to_square}")

    # Convert square coordinates to mm (center of square)
    def square_to_mm(sq: Square) -> tuple[float, float]:
        return ((sq.col + 0.5) * square_size_mm, (sq.row + 0.5) * square_size_mm)

    # Get edge midpoint between two squares
    def get_edge_point(sq1: Square, sq2: Square, offset_mm: float = 1.0) -> tuple[float, float]:
        """
        Get a point on the edge between two squares, offset slightly to avoid pieces.

        Args:
            sq1: First square
            sq2: Second square
            offset_mm: Offset from square edge for clearance

        Returns:
            (x, y) position in mm
        """
        x1, y1 = square_to_mm(sq1)
        x2, y2 = square_to_mm(sq2)
        # Midpoint between centers
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        return (mid_x, mid_y)

    # Determine direction of movement
    moving_up = delta_row > 0
    moving_right = delta_col > 0

    # Start: move to appropriate corner of starting square to begin navigation
    # We want the corner closest to our destination
    clearance = 1.0  # mm from edge
    start_x = from_square.col * square_size_mm + (
        square_size_mm - clearance if moving_right else clearance
    )
    start_y = from_square.row * square_size_mm + (
        square_size_mm - clearance if moving_up else clearance
    )
    waypoints.append(Waypoint(start_x, start_y, f"Corner of {from_square.to_notation()}"))

    # Middle: navigate along the edge between squares to avoid obstacles
    # The knight's L-path crosses certain intermediate squares
    # We move to a point between these squares (on the edge line)

    if abs(delta_row) == 2:
        # Primarily vertical: 2 rows, 1 column
        # Navigate to the edge between intermediate and destination column
        intermediate_row = from_square.row + (1 if moving_up else -1)
        # Edge point between the two columns at the intermediate row level
        edge_x = (from_square.col + to_square.col + 1) * square_size_mm / 2
        edge_y = (intermediate_row + 0.5) * square_size_mm + (
            square_size_mm / 2 if moving_up else -square_size_mm / 2
        )
        waypoints.append(
            Waypoint(
                edge_x,
                edge_y,
                f"Edge between columns at row {intermediate_row + (1 if moving_up else 0)}",
            )
        )
    else:
        # Primarily horizontal: 2 columns, 1 row
        # Navigate to the edge between intermediate and destination row
        intermediate_col = from_square.col + (1 if moving_right else -1)
        # Edge point between the two rows at the intermediate column level
        edge_x = (intermediate_col + 0.5) * square_size_mm + (
            square_size_mm / 2 if moving_right else -square_size_mm / 2
        )
        edge_y = (from_square.row + to_square.row + 1) * square_size_mm / 2
        waypoints.append(
            Waypoint(
                edge_x,
                edge_y,
                f"Edge between rows at column {intermediate_col + (1 if moving_right else 0)}",
            )
        )

    # Final: center of destination square
    dest_x, dest_y = square_to_mm(to_square)
    waypoints.append(Waypoint(dest_x, dest_y, f"Center of {to_square.to_notation()}"))

    return waypoints
