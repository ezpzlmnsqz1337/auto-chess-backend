"""High-level piece movement with magnet control and obstacle avoidance.

This module provides the main interface for moving chess pieces on the automated board.
It handles:
- Magnet activation/deactivation
- Obstacle avoidance (knights and capture area movements)
- Coordinated motor movements
"""

import config
from chess_game import ChessGame, Square
from motor import MotorController
from src.board_navigation import extended_square_to_steps, square_to_steps
from src.knight_pathfinding import plan_knight_movement


def _plan_capture_area_path(
    from_square: Square,
    capture_row: int,
    capture_col: int,
    game: ChessGame | None,
    occupied_capture_squares: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    """
    Plan a path to move a piece from the board to the capture area, avoiding obstacles.

    Uses greedy local pathfinding:
    1. Try to move horizontally toward target
    2. If blocked, try diagonal moves
    3. If still blocked, move vertically
    4. As last resort, use edge routing

    Args:
        from_square: Source square on the main board
        capture_row: Row in capture area (0-7)
        capture_col: Column in capture area (-2, -1 for left; 8, 9 for right)
        game: Optional game state for obstacle detection
        occupied_capture_squares: Set of (row, col) tuples for occupied capture area squares

    Returns:
        List of (x, y) waypoints in motor steps
    """
    from_x, from_y = square_to_steps(from_square.row, from_square.col)
    to_x, to_y = extended_square_to_steps(capture_row, capture_col)

    # If no game state, use direct path
    if game is None:
        return [(to_x, to_y)]

    # Determine which side we're going to
    is_left_capture = capture_col < 0

    waypoints: list[tuple[int, int]] = []

    # Start from current position
    current_row = from_square.row
    current_col = from_square.col

    # Target edge column (0 for left capture, 7 for right capture)
    target_edge_col = 0 if is_left_capture else 7

    # Helper function to check if a square is occupied (excluding the starting square)
    def is_occupied(row: int, col: int) -> bool:
        """Check if a square is occupied, excluding the piece being moved."""
        test_square = Square(row, col)
        # The starting square is not an obstacle since we're moving the piece from there
        if test_square == from_square:
            return False
        return test_square in game.board

    # Keep moving until we reach the target edge column
    # BUT if we're on an edge row (0 or 7) and completely blocked, we can enter the capture area
    # directly from wherever we are on that row
    max_iterations = 100  # Safety limit to prevent infinite loops
    iteration = 0
    last_position = (current_row, current_col)

    while current_col != target_edge_col and iteration < max_iterations:
        iteration += 1

        # Check if we're stuck (position hasn't changed for multiple iterations)
        if (
            iteration > 1
            and (current_row, current_col) == last_position
            and (current_row == 0 or current_row == 7)
        ):
            # We're stuck on an edge row - just enter the capture area from here
            break  # Exit loop and proceed directly to capture area
        last_position = (current_row, current_col)
        iteration += 1

        # Determine horizontal direction (-1 for left, +1 for right)
        col_direction = -1 if is_left_capture else 1
        next_col = current_col + col_direction

        # Try to move horizontally toward target
        if 0 <= next_col < config.BOARD_COLS and not is_occupied(current_row, next_col):
            # Move horizontally
            current_col = next_col
            waypoints.append(square_to_steps(current_row, current_col))
            continue

        # Horizontal move blocked, try diagonal moves (up and down)
        moved = False
        for row_direction in [1, -1]:  # Try both up and down
            next_row = current_row + row_direction
            if (
                0 <= next_row < config.BOARD_ROWS
                and 0 <= next_col < config.BOARD_COLS
                and not is_occupied(next_row, next_col)
            ):
                # Move diagonally
                current_row = next_row
                current_col = next_col
                waypoints.append(square_to_steps(current_row, current_col))
                moved = True
                break

        if moved:
            continue

        # Diagonal moves blocked, try moving vertically
        # Choose direction based on target capture row
        if current_row < capture_row:
            vertical_direction = 1  # Move up
        elif current_row > capture_row:
            vertical_direction = -1  # Move down
        else:
            # Same row as target, try moving away from crowded area
            vertical_direction = 1 if current_row < 4 else -1

        next_row = current_row + vertical_direction
        if 0 <= next_row < config.BOARD_ROWS and not is_occupied(next_row, current_col):
            # Move vertically
            current_row = next_row
            waypoints.append(square_to_steps(current_row, current_col))
            continue

        # Last resort: edge routing - try to reach an edge row
        for edge_row in [7, 0]:  # Try top then bottom edge
            # Check if we can reach this edge row vertically
            can_reach = True
            start = min(current_row, edge_row)
            end = max(current_row, edge_row)
            for r in range(start, end + 1):
                if r == current_row:
                    continue
                if is_occupied(r, current_col):
                    can_reach = False
                    break

            if can_reach:
                # Move to edge row
                current_row = edge_row
                waypoints.append(square_to_steps(current_row, current_col))
                break

    # Now at the target edge column (0 or 7), move into the capture area
    # Use the inner capture column (-1 for left, 8 for right) as the default corridor
    if current_row != capture_row:
        # Inner capture column (less likely to be filled)
        inner_capture_col = -1 if is_left_capture else 8
        outer_capture_col = -2 if is_left_capture else 9

        # Move into inner capture column at current row
        travel_col = inner_capture_col
        capture_x, capture_y = extended_square_to_steps(current_row, travel_col)
        waypoints.append((capture_x, capture_y))

        # Move vertically toward target row, checking for obstacles
        row_direction = 1 if capture_row > current_row else -1
        while current_row != capture_row:
            next_row = current_row + row_direction

            # Check if next position in current column is occupied
            next_occupied = (
                occupied_capture_squares is not None
                and (next_row, travel_col) in occupied_capture_squares
            )

            if next_occupied:
                # Current column is blocked at next_row
                # Try the other column at next_row (diagonal move)
                other_col = (
                    outer_capture_col if travel_col == inner_capture_col else inner_capture_col
                )
                other_col_next_occupied = (
                    occupied_capture_squares is not None
                    and (next_row, other_col) in occupied_capture_squares
                )

                if not other_col_next_occupied:
                    # Other column is free at next_row - move diagonally
                    travel_col = other_col
                else:
                    # Both columns blocked at next_row
                    # Move horizontally to other column at current row first
                    other_col_current_occupied = (
                        occupied_capture_squares is not None
                        and (current_row, other_col) in occupied_capture_squares
                    )
                    if not other_col_current_occupied:
                        # Switch columns at current row
                        switch_x, switch_y = extended_square_to_steps(current_row, other_col)
                        waypoints.append((switch_x, switch_y))
                        travel_col = other_col
                    # If we can't switch (both columns occupied at current row too),
                    # we're stuck - this shouldn't happen in normal gameplay

            # Move to next row in the current column
            current_row = next_row
            next_x, next_y = extended_square_to_steps(current_row, travel_col)
            waypoints.append((next_x, next_y))
    else:
        # Already at the target row, just move into the capture area
        pass

    # Finally, move into the capture area at target position
    waypoints.append((to_x, to_y))

    return waypoints if waypoints else [(to_x, to_y)]


def travel(
    controller: MotorController,
    target_x: int,
    target_y: int,
) -> None:
    """
    Move the magnet to a target position without picking up a piece.

    The electromagnet is turned OFF during this movement.

    Args:
        controller: Motor controller instance
        target_x: Target X position in motor steps
        target_y: Target Y position in motor steps
    """
    assert controller.electromagnet is not None, "Controller must have electromagnet"
    controller.electromagnet.off()
    controller.move_to(target_x, target_y)


def move_piece(
    controller: MotorController,
    from_square: Square,
    to_square: Square,
    game: ChessGame | None = None,
) -> None:
    """
    Move a chess piece from one square to another with proper magnet control.

    This is the high-level method for moving pieces on the board. It:
    1. Travels to the source square (magnet OFF)
    2. Activates the electromagnet
    3. Moves the piece to the destination (magnet ON, with obstacle avoidance if needed)
    4. Deactivates the electromagnet

    For knight moves, automatically uses obstacle avoidance if a game state is provided.

    Args:
        controller: Motor controller instance
        from_square: Source square (where the piece currently is)
        to_square: Destination square (where to move the piece)
        game: Optional ChessGame instance for obstacle detection (enables knight pathfinding)
    """
    # Convert squares to motor steps
    from_x, from_y = square_to_steps(from_square.row, from_square.col)
    to_x, to_y = square_to_steps(to_square.row, to_square.col)

    # Step 1: Travel to source square (magnet OFF)
    travel(controller, from_x, from_y)

    # Step 2: Activate magnet to grab the piece
    assert controller.electromagnet is not None, "Controller must have electromagnet"
    controller.electromagnet.on()

    # Step 3: Move piece to destination (magnet ON)
    # Check if this is a knight move and if we have game state for obstacle detection
    if game is not None:
        piece = game.board.get(from_square)
        if piece and piece.piece_type.name == "KNIGHT":
            # Use knight pathfinding with obstacle avoidance
            movement_plan = plan_knight_movement(from_square, to_square, game)

            # Execute the planned waypoints
            for waypoint_x, waypoint_y in movement_plan.waypoints:
                controller.move_to(waypoint_x, waypoint_y)
        else:
            # Direct movement for non-knight pieces
            controller.move_to(to_x, to_y)
    else:
        # No game state provided, use direct movement
        controller.move_to(to_x, to_y)

    # Step 4: Deactivate magnet to release the piece
    controller.electromagnet.off()


def move_piece_to_capture_area(
    controller: MotorController,
    from_square: Square,
    capture_row: int,
    capture_col: int,
    game: ChessGame | None = None,
    occupied_capture_squares: set[tuple[int, int]] | None = None,
) -> None:
    """
    Move a piece from the board to the capture area with obstacle avoidance.

    Uses extended board coordinates that include capture areas.
    If a game state is provided, plans a path around obstacles on the board.

    Args:
        controller: Motor controller instance
        from_square: Source square on the main board
        capture_row: Row in capture area (0-7)
        capture_col: Column in capture area (-2, -1 for left; 8, 9 for right)
        game: Optional game state for obstacle detection
        occupied_capture_squares: Set of (row, col) tuples for occupied capture area squares
    """
    # Convert source square to motor steps
    from_x, from_y = square_to_steps(from_square.row, from_square.col)

    # Step 1: Travel to source square (magnet OFF)
    travel(controller, from_x, from_y)

    # Step 2: Activate magnet to grab the piece
    assert controller.electromagnet is not None, "Controller must have electromagnet"
    controller.electromagnet.on()

    # Step 3: Move piece to capture area (magnet ON) with obstacle avoidance
    waypoints = _plan_capture_area_path(
        from_square, capture_row, capture_col, game, occupied_capture_squares
    )
    for waypoint_x, waypoint_y in waypoints:
        controller.move_to(waypoint_x, waypoint_y)

    # Step 4: Deactivate magnet to release the piece
    controller.electromagnet.off()
