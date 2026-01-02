"""Reusable movement patterns for demos and calibration."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

import config
from board_navigation import square_to_steps

if TYPE_CHECKING:
    from motor import MotorController


def get_edge_square_pattern() -> list[tuple[int, int]]:
    """Get coordinates for moving around the edge of the board (square pattern).

    Returns:
        List of (x, y) coordinates in steps for board perimeter movement.
    """
    return [
        square_to_steps(0, 0),  # a1 - bottom left
        square_to_steps(0, 7),  # h1 - bottom right
        square_to_steps(7, 7),  # h8 - top right
        square_to_steps(7, 0),  # a8 - top left
        square_to_steps(0, 0),  # back to a1
    ]


def get_diagonal_patterns() -> list[tuple[tuple[int, int], tuple[int, int], str]]:
    """Get all four major diagonal patterns.

    Returns:
        List of (start, end, name) tuples for each diagonal.
    """
    return [
        # (start, end, name)
        (square_to_steps(0, 0), square_to_steps(7, 7), "a1 → h8 (↗)"),
        (square_to_steps(0, 7), square_to_steps(7, 0), "h1 → a8 (↖)"),
        (square_to_steps(7, 0), square_to_steps(0, 7), "a8 → h1 (↘)"),
        (square_to_steps(7, 7), square_to_steps(0, 0), "h8 → a1 (↙)"),
    ]


def get_snake_pattern() -> list[tuple[int, int]]:
    """Get snake pattern visiting all 64 squares.

    Snake moves left-to-right on even rows, right-to-left on odd rows.

    Returns:
        List of (x, y) coordinates in steps for all squares.
    """
    positions = []

    for row in range(config.BOARD_ROWS):
        # Even row: go left to right (0 to 7), odd row: go right to left (7 to 0)
        cols = range(config.BOARD_COLS) if row % 2 == 0 else range(config.BOARD_COLS - 1, -1, -1)

        for col in cols:
            x, y = square_to_steps(row, col)
            positions.append((x, y))

    return positions


def execute_pattern(
    controller: "MotorController", positions: Sequence[tuple[int, int]], *, verbose: bool = True
) -> None:
    """Execute a movement pattern with the given controller.

    Args:
        controller: MotorController instance
        positions: List of (x, y) coordinates to visit
        verbose: Print progress updates
    """
    if verbose:
        print(f"Executing pattern with {len(positions)} waypoints...")

    for i, (x, y) in enumerate(positions):
        controller.move_to(x, y)
        if verbose and (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{len(positions)} waypoints")

    if verbose:
        final_x, final_y = controller.get_position()
        print(f"✓ Pattern complete. Final position: ({final_x}, {final_y})")
