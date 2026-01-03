"""Tests for capture handling with magnet movement visualization.

This module demonstrates AI capture sequences with real motor movements:
- Before capture: Shows initial board state
- Remove captured piece: Motor moves opponent piece to capture area
- Move capturing piece: Motor moves own piece to target square

Each sequence shows chess board, movement path, and speed profile.
Uses the application's piece_movement module for proper magnet control.
"""

from pathlib import Path
from typing import Any, TypedDict

import matplotlib.pyplot as plt

import config
from capture_management import get_next_capture_slot
from chess_game import ChessGame, Piece, PieceType, Player, Square
from motor import MotorController
from piece_movement import move_piece, move_piece_to_capture_area
from tests.fixtures.movement_capture import capture_movement_path_during_execution
from tests.test_utils import create_test_controller
from tests.visualization import (
    draw_movement_path,
    draw_speed_profile,
    setup_chess_board_plot,
    setup_movement_plot,
    setup_speed_plot,
    standard_draw_chess_pieces,
)


def _capture_piece_movement_to_capture_area(
    controller: MotorController,
    from_square: Square,
    capture_row: int,
    capture_col: int,
    game: ChessGame | None = None,
    occupied_capture_squares: set[tuple[int, int]] | None = None,
) -> tuple[list[float], list[float], list[bool], list[float], list[float]]:
    """
    Wrapper to capture movement path when moving a piece to capture area.

    Uses the application's move_piece_to_capture_area while recording the path.
    """
    positions, timestamps, speeds, magnet_states = capture_movement_path_during_execution(
        controller,
        lambda: move_piece_to_capture_area(
            controller, from_square, capture_row, capture_col, game, occupied_capture_squares
        ),
        sample_rate=20,
    )

    path_x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    path_y_mm = [y / config.STEPS_PER_MM for _, y in positions]

    return path_x_mm, path_y_mm, magnet_states, speeds, timestamps


def _capture_piece_movement(
    controller: MotorController,
    from_square: Square,
    to_square: Square,
    game: ChessGame | None = None,
) -> tuple[list[float], list[float], list[bool], list[float], list[float]]:
    """
    Wrapper to capture movement path when moving a piece between squares.

    Uses the application's move_piece while recording the path.
    """
    positions, timestamps, speeds, magnet_states = capture_movement_path_during_execution(
        controller, lambda: move_piece(controller, from_square, to_square, game), sample_rate=20
    )

    path_x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    path_y_mm = [y / config.STEPS_PER_MM for _, y in positions]

    return path_x_mm, path_y_mm, magnet_states, speeds, timestamps


# Create output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "captures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class CaptureState(TypedDict):
    """Type definition for capture sequence state."""

    game: ChessGame
    title: str
    subtitle: str
    path_x: list[float]
    path_y: list[float]
    magnet_states: list[bool]
    speeds: list[float]
    time: list[float]


def test_knight_captures_pawn() -> None:
    """Test knight capturing pawn with complete movement visualization.

    Scenario: White knight on b1 captures black pawn on c3.

    Shows:
    1. Before capture: Initial board state
    2. Remove pawn: Move black pawn from c3 to capture area
    3. Move knight: Move white knight from b1 to c3
    """
    # Setup initial board state
    game = ChessGame()
    game.board.clear()

    # Place pieces for the capture scenario
    knight_square = Square.from_notation("b1")
    pawn_square = Square.from_notation("c3")

    game.board[knight_square] = Piece(PieceType.KNIGHT, Player.WHITE)
    game.board[pawn_square] = Piece(PieceType.PAWN, Player.BLACK)

    # Get capture area placement for black pawn
    occupied_capture_squares: set[tuple[int, int]] = set()
    capture_placement = get_next_capture_slot(
        captured_piece=Piece(PieceType.PAWN, Player.BLACK),
        occupied_capture_squares=occupied_capture_squares,
    )

    assert capture_placement is not None, "Should find placement for first captured piece"

    # Create motor controller
    controller = create_test_controller()

    # State 1: Before capture
    state1_game = ChessGame()
    state1_game.board.clear()
    state1_game.board[knight_square] = Piece(PieceType.KNIGHT, Player.WHITE)
    state1_game.board[pawn_square] = Piece(PieceType.PAWN, Player.BLACK)

    # State 2: Remove captured pawn to capture area
    path_x_mm_2, path_y_mm_2, magnet_states_2, speeds_2, timestamps_2 = (
        _capture_piece_movement_to_capture_area(
            controller, pawn_square, capture_placement.row, capture_placement.col
        )
    )

    state2_game = ChessGame()
    state2_game.board.clear()
    state2_game.board[knight_square] = Piece(PieceType.KNIGHT, Player.WHITE)
    # Pawn moved to capture area (not shown on main board)

    # State 3: Move knight to capture square
    path_x_mm_3, path_y_mm_3, magnet_states_3, speeds_3, timestamps_3 = _capture_piece_movement(
        controller, knight_square, pawn_square
    )

    state3_game = ChessGame()
    state3_game.board.clear()
    state3_game.board[pawn_square] = Piece(PieceType.KNIGHT, Player.WHITE)
    # Knight now on c3, pawn removed

    # Create 3x3 plot (no LED row needed)
    fig = plt.figure(figsize=(18, 18))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.25)

    states: list[CaptureState] = [
        {
            "game": state1_game,
            "title": "1. Before Capture",
            "subtitle": "Knight on b1, Pawn on c3",
            "path_x": [],
            "path_y": [],
            "magnet_states": [],
            "speeds": [],
            "time": [],
        },
        {
            "game": state2_game,
            "title": "2. Remove Captured Piece",
            "subtitle": "Move pawn c3 → capture area",
            "path_x": path_x_mm_2,
            "path_y": path_y_mm_2,
            "magnet_states": magnet_states_2,
            "speeds": speeds_2,
            "time": timestamps_2,
        },
        {
            "game": state3_game,
            "title": "3. Move Capturing Piece",
            "subtitle": "Move knight b1 → c3",
            "path_x": path_x_mm_3,
            "path_y": path_y_mm_3,
            "magnet_states": magnet_states_3,
            "speeds": speeds_3,
            "time": timestamps_3,
        },
    ]

    for col_idx, state in enumerate(states):
        # Row 1: Chess board with pieces
        ax1 = fig.add_subplot(gs[0, col_idx])
        setup_chess_board_plot(
            ax1, title=f"{state['title']}\n{state['subtitle']}", show_coordinates=True
        )
        standard_draw_chess_pieces(ax1, state["game"])

        # Row 2: Magnet movement path
        ax2 = fig.add_subplot(gs[1, col_idx])
        setup_movement_plot(ax2, title="Magnet Movement", show_capture_areas=True)

        if state["path_x"] and state["path_y"]:
            draw_movement_path(ax2, state["path_x"], state["path_y"], state["magnet_states"])

        # Row 3: Speed profile
        ax3 = fig.add_subplot(gs[2, col_idx])
        setup_speed_plot(ax3, title="Magnet Speed Profile")
        if state["time"] and state["speeds"]:
            draw_speed_profile(ax3, state["time"], state["speeds"])

    fig.suptitle(
        "AI Capture Sequence: Knight takes Pawn (Bxc3)\nWith Real Motor Movement & Acceleration",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    # Save plot
    output_path = OUTPUT_DIR / "knight_captures_pawn.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ Knight captures pawn visualization saved: {output_path}")


def test_pawn_captures_pawn() -> None:
    """Test pawn capturing pawn with diagonal movement.

    Scenario: White pawn on d4 captures black pawn on e5.

    Shows:
    1. Before capture: Initial board state
    2. Remove pawn: Move black pawn from e5 to capture area
    3. Move pawn: Move white pawn from d4 to e5
    """
    # Setup initial board state
    game = ChessGame()
    game.board.clear()

    # Place pieces for the capture scenario
    white_pawn_square = Square.from_notation("d4")
    black_pawn_square = Square.from_notation("e5")

    game.board[white_pawn_square] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[black_pawn_square] = Piece(PieceType.PAWN, Player.BLACK)

    # Get capture area placement for black pawn
    occupied_capture_squares: set[tuple[int, int]] = set()
    capture_placement = get_next_capture_slot(
        captured_piece=Piece(PieceType.PAWN, Player.BLACK),
        occupied_capture_squares=occupied_capture_squares,
    )

    assert capture_placement is not None

    # Create motor controller
    controller = create_test_controller()

    # State 1: Before capture
    state1_game = ChessGame()
    state1_game.board.clear()
    state1_game.board[white_pawn_square] = Piece(PieceType.PAWN, Player.WHITE)
    state1_game.board[black_pawn_square] = Piece(PieceType.PAWN, Player.BLACK)

    # State 2: Remove captured pawn to capture area
    path_x_mm_2, path_y_mm_2, magnet_states_2, speeds_2, timestamps_2 = (
        _capture_piece_movement_to_capture_area(
            controller, black_pawn_square, capture_placement.row, capture_placement.col
        )
    )

    state2_game = ChessGame()
    state2_game.board.clear()
    state2_game.board[white_pawn_square] = Piece(PieceType.PAWN, Player.WHITE)

    # State 3: Move white pawn to capture square (diagonal)
    path_x_mm_3, path_y_mm_3, magnet_states_3, speeds_3, timestamps_3 = _capture_piece_movement(
        controller, white_pawn_square, black_pawn_square
    )

    state3_game = ChessGame()
    state3_game.board.clear()
    state3_game.board[black_pawn_square] = Piece(PieceType.PAWN, Player.WHITE)

    # Create 3x3 plot
    fig = plt.figure(figsize=(18, 18))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.25)

    states: list[CaptureState] = [
        {
            "game": state1_game,
            "title": "1. Before Capture",
            "subtitle": "White pawn d4, Black pawn e5",
            "path_x": [],
            "path_y": [],
            "magnet_states": [],
            "speeds": [],
            "time": [],
        },
        {
            "game": state2_game,
            "title": "2. Remove Captured Piece",
            "subtitle": "Move pawn e5 → capture area",
            "path_x": path_x_mm_2,
            "path_y": path_y_mm_2,
            "magnet_states": magnet_states_2,
            "speeds": speeds_2,
            "time": timestamps_2,
        },
        {
            "game": state3_game,
            "title": "3. Move Capturing Piece",
            "subtitle": "Move pawn d4 → e5 (diagonal)",
            "path_x": path_x_mm_3,
            "path_y": path_y_mm_3,
            "magnet_states": magnet_states_3,
            "speeds": speeds_3,
            "time": timestamps_3,
        },
    ]

    for col_idx, state in enumerate(states):
        # Row 1: Chess board with pieces
        ax1 = fig.add_subplot(gs[0, col_idx])
        setup_chess_board_plot(
            ax1, title=f"{state['title']}\n{state['subtitle']}", show_coordinates=True
        )
        standard_draw_chess_pieces(ax1, state["game"])

        # Row 2: Magnet movement path
        ax2 = fig.add_subplot(gs[1, col_idx])
        setup_movement_plot(ax2, title="Magnet Movement", show_capture_areas=True)

        if state["path_x"] and state["path_y"]:
            draw_movement_path(ax2, state["path_x"], state["path_y"], state["magnet_states"])

        # Row 3: Speed profile
        ax3 = fig.add_subplot(gs[2, col_idx])
        setup_speed_plot(ax3, title="Magnet Speed Profile")
        if state["time"] and state["speeds"]:
            draw_speed_profile(ax3, state["time"], state["speeds"])

    fig.suptitle(
        "AI Capture Sequence: Pawn takes Pawn (dxe5)\nDiagonal Pawn Capture with Movement",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    # Save plot
    output_path = OUTPUT_DIR / "pawn_captures_pawn.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ Pawn captures pawn visualization saved: {output_path}")


def test_bishop_captures_knight() -> None:
    """Test bishop capturing knight with long diagonal movement.

    Scenario: White bishop on c1 captures black knight on f4.

    Shows:
    1. Before capture: Initial board state
    2. Remove knight: Move black knight from f4 to capture area
    3. Move bishop: Move white bishop from c1 to f4 (long diagonal)
    """
    # Setup initial board state
    game = ChessGame()
    game.board.clear()

    # Place pieces for the capture scenario
    bishop_square = Square.from_notation("c1")
    knight_square = Square.from_notation("f4")

    game.board[bishop_square] = Piece(PieceType.BISHOP, Player.WHITE)
    game.board[knight_square] = Piece(PieceType.KNIGHT, Player.BLACK)

    # Get capture area placement for black knight
    occupied_capture_squares: set[tuple[int, int]] = set()
    capture_placement = get_next_capture_slot(
        captured_piece=Piece(PieceType.KNIGHT, Player.BLACK),
        occupied_capture_squares=occupied_capture_squares,
    )

    assert capture_placement is not None

    # Create motor controller
    controller = create_test_controller()

    # State 1: Before capture
    state1_game = ChessGame()
    state1_game.board.clear()
    state1_game.board[bishop_square] = Piece(PieceType.BISHOP, Player.WHITE)
    state1_game.board[knight_square] = Piece(PieceType.KNIGHT, Player.BLACK)

    # State 2: Remove captured knight to capture area
    path_x_mm_2, path_y_mm_2, magnet_states_2, speeds_2, timestamps_2 = (
        _capture_piece_movement_to_capture_area(
            controller, knight_square, capture_placement.row, capture_placement.col
        )
    )

    state2_game = ChessGame()
    state2_game.board.clear()
    state2_game.board[bishop_square] = Piece(PieceType.BISHOP, Player.WHITE)

    # State 3: Move bishop to capture square (long diagonal)
    path_x_mm_3, path_y_mm_3, magnet_states_3, speeds_3, timestamps_3 = _capture_piece_movement(
        controller, bishop_square, knight_square
    )

    state3_game = ChessGame()
    state3_game.board.clear()
    state3_game.board[knight_square] = Piece(PieceType.BISHOP, Player.WHITE)

    # Create 3x3 plot
    fig = plt.figure(figsize=(18, 18))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.25)

    states: list[CaptureState] = [
        {
            "game": state1_game,
            "title": "1. Before Capture",
            "subtitle": "Bishop c1, Knight f4",
            "path_x": [],
            "path_y": [],
            "magnet_states": [],
            "speeds": [],
            "time": [],
        },
        {
            "game": state2_game,
            "title": "2. Remove Captured Piece",
            "subtitle": "Move knight f4 → capture area",
            "path_x": path_x_mm_2,
            "path_y": path_y_mm_2,
            "magnet_states": magnet_states_2,
            "speeds": speeds_2,
            "time": timestamps_2,
        },
        {
            "game": state3_game,
            "title": "3. Move Capturing Piece",
            "subtitle": "Move bishop c1 → f4 (long diagonal)",
            "path_x": path_x_mm_3,
            "path_y": path_y_mm_3,
            "magnet_states": magnet_states_3,
            "speeds": speeds_3,
            "time": timestamps_3,
        },
    ]

    for col_idx, state in enumerate(states):
        # Row 1: Chess board with pieces
        ax1 = fig.add_subplot(gs[0, col_idx])
        setup_chess_board_plot(
            ax1, title=f"{state['title']}\n{state['subtitle']}", show_coordinates=True
        )
        standard_draw_chess_pieces(ax1, state["game"])

        # Row 2: Magnet movement path
        ax2 = fig.add_subplot(gs[1, col_idx])
        setup_movement_plot(ax2, title="Magnet Movement", show_capture_areas=True)

        if state["path_x"] and state["path_y"]:
            draw_movement_path(ax2, state["path_x"], state["path_y"], state["magnet_states"])

        # Row 3: Speed profile
        ax3 = fig.add_subplot(gs[2, col_idx])
        setup_speed_plot(ax3, title="Magnet Speed Profile")
        if state["time"] and state["speeds"]:
            draw_speed_profile(ax3, state["time"], state["speeds"])

    fig.suptitle(
        "AI Capture Sequence: Bishop takes Knight (Bxf4)\nLong Diagonal Movement with Acceleration",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    # Save plot
    output_path = OUTPUT_DIR / "bishop_captures_knight.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ Bishop captures knight visualization saved: {output_path}")


def test_queen_captures_pawn_with_obstacles() -> None:
    """Test queen capturing pawn on populated board with obstacle avoidance.

    Scenario: Mid-game position where white queen on e4 captures black pawn on e7.
    The board has pieces blocking the direct path, demonstrating obstacle avoidance
    when moving the captured piece to the capture area.

    The path planning will route around occupied squares by:
    - Moving to the edge of the board first
    - Then moving horizontally to the capture area
    - Finally positioning in the target capture square

    Shows:
    1. Before capture: Mid-game board state with multiple pieces
    2. Remove pawn: Move black pawn from e7 to capture area (with obstacle avoidance!)
    3. Move queen: Move white queen from e4 to e7 (straight vertical)
    """
    # Setup mid-game board state with multiple pieces
    game = ChessGame()
    game.board.clear()

    # Place white pieces (realistic mid-game position)
    game.board[Square.from_notation("e4")] = Piece(PieceType.QUEEN, Player.WHITE)
    game.board[Square.from_notation("e1")] = Piece(PieceType.KING, Player.WHITE)
    game.board[Square.from_notation("a1")] = Piece(PieceType.ROOK, Player.WHITE)
    game.board[Square.from_notation("h1")] = Piece(PieceType.ROOK, Player.WHITE)
    game.board[Square.from_notation("c1")] = Piece(PieceType.BISHOP, Player.WHITE)
    game.board[Square.from_notation("f1")] = Piece(PieceType.BISHOP, Player.WHITE)
    game.board[Square.from_notation("b1")] = Piece(PieceType.KNIGHT, Player.WHITE)
    game.board[Square.from_notation("g1")] = Piece(PieceType.KNIGHT, Player.WHITE)
    game.board[Square.from_notation("a2")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("b2")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("c2")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("d3")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("f2")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("g2")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("h2")] = Piece(PieceType.PAWN, Player.WHITE)

    # Place black pieces - WITH OBSTACLES in the path to left capture area!
    game.board[Square.from_notation("e8")] = Piece(PieceType.KING, Player.BLACK)
    game.board[Square.from_notation("d8")] = Piece(PieceType.QUEEN, Player.BLACK)
    game.board[Square.from_notation("a8")] = Piece(PieceType.ROOK, Player.BLACK)
    game.board[Square.from_notation("h8")] = Piece(PieceType.ROOK, Player.BLACK)
    game.board[Square.from_notation("c8")] = Piece(PieceType.BISHOP, Player.BLACK)
    game.board[Square.from_notation("f8")] = Piece(PieceType.BISHOP, Player.BLACK)
    game.board[Square.from_notation("b8")] = Piece(PieceType.KNIGHT, Player.BLACK)
    game.board[Square.from_notation("g8")] = Piece(PieceType.KNIGHT, Player.BLACK)
    game.board[Square.from_notation("a7")] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square.from_notation("b7")] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square.from_notation("c7")] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square.from_notation("d7")] = Piece(PieceType.PAWN, Player.BLACK)  # Obstacle!
    game.board[Square.from_notation("e7")] = Piece(PieceType.PAWN, Player.BLACK)  # Target
    game.board[Square.from_notation("f7")] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square.from_notation("g7")] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square.from_notation("h7")] = Piece(PieceType.PAWN, Player.BLACK)
    game.board[Square.from_notation("d5")] = Piece(PieceType.PAWN, Player.BLACK)

    # Define squares involved in capture
    queen_square = Square.from_notation("e4")
    pawn_square = Square.from_notation("e7")

    # Get capture area placement for black pawn
    occupied_capture_squares: set[tuple[int, int]] = set()

    # Add already captured pieces in the capture area to test obstacle avoidance
    # These will block the direct path through the capture area
    occupied_capture_squares.add((3, -1))  # Row 3, inner left capture column
    occupied_capture_squares.add((4, -2))  # Row 4, outer left capture column

    capture_placement = get_next_capture_slot(
        captured_piece=Piece(PieceType.PAWN, Player.BLACK),
        occupied_capture_squares=occupied_capture_squares,
    )
    assert capture_placement is not None
    # NOTE: Do NOT add capture_placement to occupied_capture_squares before planning path
    # The destination is where we're going, not an obstacle to avoid!

    controller = create_test_controller()

    # State 1: Before capture
    state1_game = ChessGame()
    state1_game.board = game.board.copy()

    # State 2: Remove captured pawn to capture area WITH OBSTACLE AVOIDANCE
    path_x_mm_2, path_y_mm_2, magnet_states_2, speeds_2, timestamps_2 = (
        _capture_piece_movement_to_capture_area(
            controller,
            pawn_square,
            capture_placement.row,
            capture_placement.col,
            game,
            occupied_capture_squares,  # Does NOT include the destination
        )
    )

    state2_game = ChessGame()
    state2_game.board = game.board.copy()
    del state2_game.board[pawn_square]

    # State 3: Move capturing queen
    path_x_mm_3, path_y_mm_3, magnet_states_3, speeds_3, timestamps_3 = _capture_piece_movement(
        controller, queen_square, pawn_square, game
    )

    state3_game = ChessGame()
    state3_game.board = state2_game.board.copy()
    del state3_game.board[queen_square]
    state3_game.board[pawn_square] = Piece(PieceType.QUEEN, Player.WHITE)

    # Create 3x3 grid visualization
    fig = plt.figure(figsize=(18, 18))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    states: list[CaptureState] = [
        {
            "game": state1_game,
            "title": "1. Before Capture",
            "subtitle": "Queen on e4, Target Pawn on e7\nObstacles: Pawns on d7, d5",
            "path_x": [],
            "path_y": [],
            "magnet_states": [],
            "speeds": [],
            "time": [],
        },
        {
            "game": state2_game,
            "title": "2. Remove Captured Piece",
            "subtitle": f"Pawn e7 → Capture Area ({capture_placement.col}, {capture_placement.row})\nPath Routes Around Obstacles!",
            "path_x": path_x_mm_2,
            "path_y": path_y_mm_2,
            "magnet_states": magnet_states_2,
            "speeds": speeds_2,
            "time": timestamps_2,
        },
        {
            "game": state3_game,
            "title": "3. Move Capturing Piece",
            "subtitle": "Queen e4 → e7\nStraight Vertical Path",
            "path_x": path_x_mm_3,
            "path_y": path_y_mm_3,
            "magnet_states": magnet_states_3,
            "speeds": speeds_3,
            "time": timestamps_3,
        },
    ]

    for col_idx, state in enumerate(states):
        # Row 0: Chess board
        ax_board = fig.add_subplot(gs[0, col_idx])
        setup_chess_board_plot(
            ax_board, title=f"{state['title']}\n{state['subtitle']}", show_capture_areas=True
        )
        standard_draw_chess_pieces(ax_board, state["game"])

        # Draw captured pieces in capture area for states 2 and 3
        if col_idx >= 1:  # States 2 and 3 have captured pieces
            # Draw the previously captured pieces as actual chess pieces
            # Need to convert extended column coordinates to board plot coordinates
            gap_in_squares = config.CAPTURE_OFFSET_MM / config.SQUARE_SIZE_MM
            left_capture_start = -(config.CAPTURE_COLS + gap_in_squares)

            for cap_row, cap_col in [(3, -1), (4, -2)]:
                # Convert extended column to plot x position
                # Column -1 is the inner column (index 1 from left edge)
                # Column -2 is the outer column (index 0 from left edge)
                col_index = cap_col + 2  # Convert -2→0, -1→1
                x_pos = left_capture_start + col_index + 0.5

                # Draw black pawn in capture area
                ax_board.text(
                    x_pos,
                    cap_row + 0.5,
                    "♟",
                    fontsize=20,
                    ha="center",
                    va="center",
                    color="black",
                    weight="bold",
                    zorder=10,
                )

        # Row 1: Movement plot
        ax_movement = fig.add_subplot(gs[1, col_idx])
        setup_movement_plot(ax_movement, title="Magnet Movement", show_capture_areas=True)
        if state["path_x"]:
            draw_movement_path(
                ax_movement, state["path_x"], state["path_y"], state["magnet_states"]
            )

        # Row 2: Speed plot
        ax_speed = fig.add_subplot(gs[2, col_idx])
        setup_speed_plot(ax_speed, title="Magnet Speed Profile")
        if state["speeds"]:
            draw_speed_profile(ax_speed, state["time"], state["speeds"])

    fig.suptitle(
        "AI Capture Sequence: Queen takes Pawn (Qxe7)\nWith Obstacle Avoidance Path Planning",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    # Save plot
    output_path = OUTPUT_DIR / "queen_captures_pawn_obstacles.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ Queen captures pawn (with obstacle avoidance) visualization saved: {output_path}")


def test_black_knight_captures_white_pawn_with_obstacles() -> None:
    """Black Knight captures White Pawn with obstacles in right capture area.

    Tests obstacle avoidance for capturing white pieces:
    - Black Knight moves from d4 to e2
    - Captures white pawn at e2
    - Routes pawn to right capture area (columns 8, 9) with obstacles
    - Obstacles at (3, 8) and (4, 9) force diagonal navigation
    """
    # Set up game state with obstacles
    game = ChessGame()

    # Place white pieces - with obstacles on edges
    game.board[Square.from_notation("a1")] = Piece(PieceType.ROOK, Player.WHITE)
    game.board[Square.from_notation("h1")] = Piece(PieceType.ROOK, Player.WHITE)
    game.board[Square.from_notation("b1")] = Piece(PieceType.KNIGHT, Player.WHITE)
    game.board[Square.from_notation("g1")] = Piece(PieceType.KNIGHT, Player.WHITE)
    game.board[Square.from_notation("c1")] = Piece(PieceType.BISHOP, Player.WHITE)
    game.board[Square.from_notation("f1")] = Piece(PieceType.BISHOP, Player.WHITE)
    game.board[Square.from_notation("d1")] = Piece(PieceType.QUEEN, Player.WHITE)
    game.board[Square.from_notation("e1")] = Piece(PieceType.KING, Player.WHITE)

    # White pawns on row 1
    for col in range(8):
        game.board[Square(1, col)] = Piece(PieceType.PAWN, Player.WHITE)

    # Add white pieces in the middle - WITH OBSTACLES in path to right capture area!
    game.board[Square.from_notation("c3")] = Piece(PieceType.PAWN, Player.WHITE)
    game.board[Square.from_notation("e2")] = Piece(PieceType.PAWN, Player.WHITE)  # Target
    game.board[Square.from_notation("f3")] = Piece(PieceType.PAWN, Player.WHITE)

    # Place black pieces
    game.board[Square.from_notation("e8")] = Piece(PieceType.KING, Player.BLACK)
    game.board[Square.from_notation("d8")] = Piece(PieceType.QUEEN, Player.BLACK)
    game.board[Square.from_notation("a8")] = Piece(PieceType.ROOK, Player.BLACK)
    game.board[Square.from_notation("h8")] = Piece(PieceType.ROOK, Player.BLACK)
    game.board[Square.from_notation("c8")] = Piece(PieceType.BISHOP, Player.BLACK)
    game.board[Square.from_notation("f8")] = Piece(PieceType.BISHOP, Player.BLACK)
    game.board[Square.from_notation("d4")] = Piece(PieceType.KNIGHT, Player.BLACK)  # Capturing piece
    game.board[Square.from_notation("g8")] = Piece(PieceType.KNIGHT, Player.BLACK)

    # Black pawns
    for col in range(8):
        game.board[Square(6, col)] = Piece(PieceType.PAWN, Player.BLACK)

    # Define squares involved in capture
    knight_square = Square.from_notation("d4")
    pawn_square = Square.from_notation("e2")

    # Get capture area placement for white pawn
    occupied_capture_squares: set[tuple[int, int]] = set()

    # Add already captured pieces in the RIGHT capture area to test obstacle avoidance
    # White pieces go to RIGHT capture area (columns 8, 9)
    occupied_capture_squares.add((3, 8))   # Row 3, inner right capture column
    occupied_capture_squares.add((4, 9))   # Row 4, outer right capture column

    capture_placement = get_next_capture_slot(
        captured_piece=Piece(PieceType.PAWN, Player.WHITE),
        occupied_capture_squares=occupied_capture_squares,
    )
    assert capture_placement is not None
    # NOTE: Do NOT add capture_placement to occupied_capture_squares before planning path
    # The destination is where we're going, not an obstacle to avoid!

    controller = create_test_controller()

    # State 1: Before capture
    state1_game = ChessGame()
    state1_game.board = game.board.copy()

    # State 2: Remove captured pawn to capture area WITH OBSTACLE AVOIDANCE
    path_x_mm_2, path_y_mm_2, magnet_states_2, speeds_2, timestamps_2 = _capture_piece_movement_to_capture_area(
        controller, pawn_square, capture_placement.row, capture_placement.col, game, occupied_capture_squares
    )

    state2_game = ChessGame()
    state2_game.board = game.board.copy()
    del state2_game.board[pawn_square]

    # State 3: Move capturing knight
    path_x_mm_3, path_y_mm_3, magnet_states_3, speeds_3, timestamps_3 = _capture_piece_movement(
        controller, knight_square, pawn_square, game
    )

    state3_game = ChessGame()
    state3_game.board = game.board.copy()
    state3_game.board[pawn_square] = state3_game.board.pop(knight_square)

    # Create visualization
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    states: list[dict[str, Any]] = [
        {
            "title": "1. Before Capture\nBlack Knight on d4, White Pawn on e2\nObstacles: Pawns on c3, f3",
            "game": state1_game,
            "path_x": [],
            "path_y": [],
            "magnet_states": [],
            "speeds": [],
            "time": [],
        },
        {
            "title": "2. Remove Captured Piece\nWhite Pawn e2 → Capture Area (5,8)\nPath Routes Around Obstacles!",
            "game": state2_game,
            "path_x": path_x_mm_2,
            "path_y": path_y_mm_2,
            "magnet_states": magnet_states_2,
            "speeds": speeds_2,
            "time": timestamps_2,
        },
        {
            "title": "3. Move Capturing Piece\nBlack Knight d4 → e2",
            "game": state3_game,
            "path_x": path_x_mm_3,
            "path_y": path_y_mm_3,
            "magnet_states": magnet_states_3,
            "speeds": speeds_3,
            "time": timestamps_3,
        },
    ]

    for col_idx, state in enumerate(states):
        # Row 0: Chess board
        ax_board = fig.add_subplot(gs[0, col_idx])
        setup_chess_board_plot(ax_board, title=state["title"], show_capture_areas=True)
        standard_draw_chess_pieces(ax_board, state["game"])

        # Row 1: Movement plot
        ax_movement = fig.add_subplot(gs[1, col_idx])
        setup_movement_plot(ax_movement, title="Magnet Movement", show_capture_areas=True)
        if state["path_x"]:
            draw_movement_path(
                ax_movement, state["path_x"], state["path_y"], state["magnet_states"]
            )

        # Row 2: Speed plot
        ax_speed = fig.add_subplot(gs[2, col_idx])
        setup_speed_plot(ax_speed, title="Magnet Speed Profile")
        if state["speeds"]:
            draw_speed_profile(ax_speed, state["time"], state["speeds"])

    fig.suptitle(
        "AI Capture Sequence: Black Knight takes White Pawn (Nxe2)\nWith Obstacle Avoidance Path Planning",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    # Save plot
    output_path = OUTPUT_DIR / "black_knight_captures_white_pawn_obstacles.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ Black knight captures white pawn (with obstacle avoidance) visualization saved: {output_path}")


if __name__ == "__main__":
    print("Running capture handling tests with motor movement visualization...")
    print(f"Output directory: {OUTPUT_DIR}\n")

    test_knight_captures_pawn()
    test_pawn_captures_pawn()
    test_bishop_captures_knight()
    test_queen_captures_pawn_with_obstacles()
    test_black_knight_captures_white_pawn_with_obstacles()

    print("\n✅ All capture handling tests passed!")
    print(f"📊 Visualizations saved to: {OUTPUT_DIR}/")
