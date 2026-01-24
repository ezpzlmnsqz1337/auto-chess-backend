"""High-level piece movement with magnet control and obstacle avoidance.

This module provides the main interface for moving chess pieces on the automated board.
It handles:
- Magnet activation/deactivation
- Obstacle avoidance (knights and capture area movements)
- Coordinated motor movements
"""

from collections import deque

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

    Uses edge-based pathfinding with clearance margins (similar to knight movement),
    ensuring pieces navigate around obstacles without passing through them.

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
    target_edge_col = 0 if is_left_capture else 7

    # Helper: Check if a main board square is occupied (excluding starting square)
    def is_occupied(row: int, col: int) -> bool:
        """Check if a square is occupied, excluding the piece being moved."""
        if not (0 <= row < config.BOARD_ROWS and 0 <= col < config.BOARD_COLS):
            return True  # Out of bounds is blocked
        test_square = Square(row, col)
        if test_square == from_square:
            return False
        return test_square in game.board

    # BFS to find unobstructed path to board edge
    def find_path_to_edge(start_row: int, start_col: int) -> list[tuple[int, int]] | None:
        """Find path from (start_row, start_col) to target edge column."""
        queue_data: deque[tuple[int, int, list[tuple[int, int]]]] = deque([
            (start_row, start_col, [(start_row, start_col)])
        ])
        visited: set[tuple[int, int]] = {(start_row, start_col)}

        while queue_data:
            row, col, path = queue_data.popleft()

            # Check if we reached the target edge
            if col == target_edge_col:
                return path

            # Try all directions (cardinal + diagonal)
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                next_row, next_col = row + dr, col + dc

                if (next_row, next_col) not in visited and not is_occupied(next_row, next_col):
                    visited.add((next_row, next_col))
                    queue_data.append((next_row, next_col, path + [(next_row, next_col)]))

        return None

    # If completely boxed in on all adjacent squares, force fallback straight-line edge walk
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    all_neighbors_blocked = all(
        is_occupied(from_square.row + dr, from_square.col + dc) for dr, dc in directions
    )

    # Find path to board edge unless we're boxed in
    path_to_edge = None if all_neighbors_blocked else find_path_to_edge(from_square.row, from_square.col)

    # If path uses vertical/diagonal moves toward a side capture, force edge-walk instead
    force_edge_walk = False
    if path_to_edge:
        for (r1, c1), (r2, c2) in zip(path_to_edge, path_to_edge[1:]):
            dr, dc = r2 - r1, c2 - c1
            if capture_col >= 8:
                # For right capture, require purely horizontal toward increasing col
                if dr != 0 or dc <= 0:
                    force_edge_walk = True
                    break
            elif capture_col < 0:
                # For left capture, purely horizontal toward decreasing col
                if dr != 0 or dc >= 0:
                    force_edge_walk = True
                    break
    if force_edge_walk:
        path_to_edge = None

    # Convert board path to motor steps using edge-based navigation
    # This ensures we move along edges between squares with clearance, not through centers
    waypoints: list[tuple[int, int]] = []
    edge_row = from_square.row
    fallback_edge_walk = False

    if path_to_edge is None:
        # BFS failed - piece is surrounded. Try escape routes by finding clear vertical paths
        # Strategy: try moving to different rows, then move to edge column from there

        escape_found = False
        best_escape_path: list[tuple[int, int]] | None = None

        # Try escaping upward or downward
        for escape_col in range(8):
            # Try moving vertically to find a clear row
            for escape_row in [0, 7, 2, 5, 3, 4, 1, 6]:  # Prioritize extreme rows
                # Check if there's a clear vertical path to escape_row at escape_col
                path_is_clear = True
                direction = 1 if escape_row > from_square.row else -1
                current_row = from_square.row

                while current_row != escape_row:
                    current_row += direction
                    if is_occupied(current_row, escape_col):
                        path_is_clear = False
                        break

                if not path_is_clear:
                    continue

                # Now try to reach target edge column from this escape position
                escape_path = find_path_to_edge(escape_row, escape_col)
                if escape_path is not None:
                    best_escape_path = [
                        (from_square.row, from_square.col)
                    ]
                    # Add path from current to escape position
                    direction = 1 if escape_row > from_square.row else -1
                    for r in range(from_square.row + direction, escape_row + direction, direction):
                        best_escape_path.append((r, escape_col))
                    # Add escape path to edge
                    best_escape_path.extend(escape_path[1:])
                    escape_found = True
                    break

            if escape_found:
                break

        if escape_found and best_escape_path is not None:
            path_to_edge = best_escape_path
        else:
            # Still no path (or boxed in) - final fallback:
            # Move to square corner facing capture side, then slide along that square edge
            # to the board boundary in the capture direction, then resume capture-area nav.
            square_size_steps = int(config.SQUARE_SIZE_MM * config.STEPS_PER_MM)
            half_square_steps = square_size_steps // 2

            center_x, center_y = square_to_steps(from_square.row, from_square.col)
            corner_x = center_x - half_square_steps if is_left_capture else center_x + half_square_steps
            # Use top edge toward capture side (horizontal traverse)
            corner_y = center_y + half_square_steps

            # Board boundary at capture side (use outer edge of the edge column)
            if is_left_capture:
                boundary_x_mm = target_edge_col * config.SQUARE_SIZE_MM + config.MOTOR_X_OFFSET_MM
            else:
                boundary_x_mm = (target_edge_col + 1) * config.SQUARE_SIZE_MM + config.MOTOR_X_OFFSET_MM
            boundary_x = int(boundary_x_mm * config.STEPS_PER_MM)

            waypoints.append((corner_x, corner_y))
            waypoints.append((boundary_x, corner_y))

            edge_row = from_square.row
            fallback_edge_walk = True

    if not fallback_edge_walk and path_to_edge is not None and len(path_to_edge) > 1:
        # Use BFS path but navigate using edge-based approach
        # Move along edges between squares with clearance to avoid pieces

        square_size_steps = int(config.SQUARE_SIZE_MM * config.STEPS_PER_MM)
        clearance_steps = int(1.0 * config.STEPS_PER_MM)  # 1mm clearance from edge

        # Start from current position
        current_x, current_y = square_to_steps(from_square.row, from_square.col)
        current_row, current_col = from_square.row, from_square.col

        # Process each step in the BFS path
        for target_row, target_col in path_to_edge[1:]:  # Skip starting position
            # Calculate movement direction
            delta_row = target_row - current_row
            delta_col = target_col - current_col

            # Get center positions for current and target
            next_x, next_y = square_to_steps(target_row, target_col)

            # Calculate edge point between squares with clearance
            # This is similar to knight pathfinding - we move along the edge
            edge_x = (current_x + next_x) // 2
            edge_y = (current_y + next_y) // 2

            # Apply clearance offset based on direction
            if delta_col != 0 and delta_row != 0:
                # Diagonal movement - apply clearance to both axes
                # Clearance pulls away from potential obstacles
                moving_right = delta_col > 0
                moving_up = delta_row > 0

                edge_x += (square_size_steps - clearance_steps) if moving_right else clearance_steps
                edge_y += (square_size_steps - clearance_steps) if moving_up else clearance_steps
            elif delta_col != 0:
                # Horizontal movement - apply clearance perpendicular to direction
                moving_right = delta_col > 0
                edge_x += (square_size_steps - clearance_steps) if moving_right else clearance_steps
            elif delta_row != 0:
                # Vertical movement - apply clearance perpendicular to direction
                moving_up = delta_row > 0
                edge_y += (square_size_steps - clearance_steps) if moving_up else clearance_steps

            # Add edge waypoint if different from last
            if not waypoints or (edge_x, edge_y) != waypoints[-1]:
                waypoints.append((edge_x, edge_y))

            # Add destination square center
            waypoints.append((next_x, next_y))

            current_row = target_row
            current_col = target_col
            current_x = next_x
            current_y = next_y

        edge_row = path_to_edge[-1][0]
    # else: fallback_edge_walk keeps edge_row at starting row

    # Now navigate in capture area from board edge
    if edge_row != capture_row:
        inner_capture_col = -1 if is_left_capture else 8
        outer_capture_col = -2 if is_left_capture else 9

        current_row = edge_row
        travel_col = inner_capture_col

        # Move into capture area at current row
        capture_x, capture_y = extended_square_to_steps(current_row, travel_col)
        waypoints.append((capture_x, capture_y))

        # Move vertically toward target row
        row_direction = 1 if capture_row > current_row else -1
        while current_row != capture_row:
            next_row = current_row + row_direction

            # Check if next position is occupied
            next_occupied = (
                occupied_capture_squares is not None
                and (next_row, travel_col) in occupied_capture_squares
            )

            if next_occupied:
                # Try other column at next_row (diagonal)
                other_col = (
                    outer_capture_col if travel_col == inner_capture_col else inner_capture_col
                )
                other_col_next_occupied = (
                    occupied_capture_squares is not None
                    and (next_row, other_col) in occupied_capture_squares
                )

                if not other_col_next_occupied:
                    # Move diagonally
                    travel_col = other_col
                else:
                    # Both columns blocked - try switching at current row
                    other_col_current_occupied = (
                        occupied_capture_squares is not None
                        and (current_row, other_col) in occupied_capture_squares
                    )
                    if not other_col_current_occupied:
                        switch_x, switch_y = extended_square_to_steps(current_row, other_col)
                        waypoints.append((switch_x, switch_y))
                        travel_col = other_col

            current_row = next_row
            next_x, next_y = extended_square_to_steps(current_row, travel_col)
            waypoints.append((next_x, next_y))

    # Finally, move into the capture area at target position
    waypoints.append((to_x, to_y))

    return waypoints if waypoints else [(to_x, to_y)]


    return []



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
