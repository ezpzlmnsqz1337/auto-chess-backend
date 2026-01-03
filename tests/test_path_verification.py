"""Test to verify the path doesn't go through occupied squares."""

from src.board_navigation import steps_to_square
from src.chess_game.game import ChessGame
from src.chess_game.piece import Piece, PieceType
from src.chess_game.player import Player
from src.chess_game.square import Square
from src.piece_movement import _plan_capture_area_path


def test_verify_path_avoids_obstacles() -> None:
    """Verify that the path doesn't go through any occupied squares."""
    # Set up game state with obstacles
    game = ChessGame()

    # Add obstacles on the board (e.g., pawns on rows 0 and 7)
    for col in range(8):
        game.board[Square(0, col)] = Piece(PieceType.PAWN, Player.WHITE)
        game.board[Square(7, col)] = Piece(PieceType.PAWN, Player.BLACK)

    # Add some pieces in the middle
    game.board[Square(4, 3)] = Piece(PieceType.QUEEN, Player.WHITE)
    game.board[Square(7, 4)] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square(5, 3)] = Piece(PieceType.PAWN, Player.BLACK)

    # Set up occupied capture squares
    occupied_capture_squares: set[tuple[int, int]] = set()
    occupied_capture_squares.add((3, -1))  # Row 3, inner left capture column
    occupied_capture_squares.add((4, -2))  # Row 4, outer left capture column

    # The piece being moved to capture area
    from_square = Square(7, 4)  # e8 - the captured black pawn
    capture_row = 5
    capture_col = -2  # Left capture area, outer column

    print(f"\n{'=' * 80}")
    print(f"Testing path from {from_square} to capture area ({capture_row}, {capture_col})")
    print(f"Occupied capture squares: {occupied_capture_squares}")
    print("Board state:")
    print(f"  - Starting square {from_square}: {game.board.get(from_square, 'EMPTY')}")
    print(f"  - Row 7: {[f'{col}:{game.board.get(Square(7, col), "E")}' for col in range(8)]}")
    print(f"  - Row 0: {[f'{col}:{game.board.get(Square(0, col), "E")}' for col in range(8)]}")
    print(f"{'=' * 80}\n")

    # Get the path waypoints (in motor steps)
    waypoints = _plan_capture_area_path(
        from_square,
        capture_row,
        capture_col,
        game,
        occupied_capture_squares,
    )

    print(f"Path has {len(waypoints)} waypoints")

    # Show unique squares
    unique_squares: list[tuple[int, int]] = []
    for x_steps, y_steps in waypoints:
        row, col = steps_to_square(x_steps, y_steps)
        if not unique_squares or unique_squares[-1] != (row, col):
            unique_squares.append((row, col))

    print(f"Unique squares in path: {len(unique_squares)}")
    for row, col in unique_squares:
        if col < 0 or col > 7:
            print(f"  ({row}, {col}) - capture area")
        else:
            print(f"  ({row}, {col}) - board square {Square(row, col)}")
    print()

    # Convert waypoints back to board coordinates and verify
    # Note: The first waypoint is the starting position, which will have the piece being moved
    # So we skip it in the collision check
    errors = []
    for i, (x_steps, y_steps) in enumerate(waypoints):
        row, col = steps_to_square(x_steps, y_steps)

        # Skip the first waypoint (starting position) since the piece is there
        if i == 0:
            print(f"  → Waypoint {i}: Starting position ({row}, {col})")
            continue

        # Check if this is a capture area square (negative columns or columns 8-9)
        if col < 0 or col > 7:
            square_desc = f"capture area ({row}, {col})"
            # Check if this capture square is occupied
            if (row, col) in occupied_capture_squares:
                error = f"  ❌ COLLISION at waypoint {i}: {square_desc} is OCCUPIED!"
                errors.append(error)
                print(error)
            else:
                print(f"  ✓ Waypoint {i}: {square_desc} - clear")
        else:
            square = Square(row, col)
            square_desc = f"board square {square}"
            # Check if this board square is occupied
            if square in game.board:
                piece = game.board[square]
                error = (
                    f"  ❌ COLLISION at waypoint {i}: {square_desc} has {piece.piece_type.name}!"
                )
                errors.append(error)
                print(error)
            else:
                print(f"  ✓ Waypoint {i}: {square_desc} - clear")

    print(f"\n{'=' * 80}")
    if errors:
        print(f"❌ FAILED: Found {len(errors)} collision(s):")
        for error in errors:
            print(error)
        print(f"{'=' * 80}\n")
        raise AssertionError(f"Path goes through {len(errors)} occupied square(s)")
    else:
        print(f"✅ PASSED: All {len(waypoints)} waypoints are clear!")
        print(f"{'=' * 80}\n")
