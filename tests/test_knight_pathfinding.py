"""Test knight pathfinding with obstacle avoidance."""

from pathlib import Path

import matplotlib.pyplot as plt

import config
from chess_game import ChessGame, Piece, PieceType, Player, Square
from src.knight_pathfinding import calculate_knight_path, plan_knight_movement
from tests.test_utils import capture_movement_path, create_test_controller
from tests.visualization import (
    draw_chess_pieces,
    draw_movement_path,
    draw_speed_profile,
    draw_waypoint_markers,
    setup_chess_board_plot,
    setup_movement_plot,
    setup_speed_plot,
)

# Create output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "knight"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_knight_obstacle_avoidance() -> None:
    """
    Test knight movement with obstacle avoidance.

    Demonstrates the b1 -> c3 knight move navigating around pawns at b2 and c2.
    """
    # Set up game with empty board
    game = ChessGame()
    game.board.clear()  # Start with empty board

    # Add pieces to demonstrate obstacle avoidance
    # Knight at b1, pawns at b2 and c2 blocking the path
    game.board[Square(0, 1)] = Piece(PieceType.KNIGHT, Player.WHITE)  # b1
    game.board[Square(1, 1)] = Piece(PieceType.PAWN, Player.WHITE)  # b2
    game.board[Square(1, 2)] = Piece(PieceType.PAWN, Player.WHITE)  # c2

    # Define knight move
    from_square = Square.from_notation("b1")
    to_square = Square.from_notation("c3")

    # Get complete movement plan from application code
    movement_plan = plan_knight_movement(from_square, to_square, game)

    # Calculate waypoints for visualization (still in mm)
    waypoints = calculate_knight_path(from_square, to_square, game, config.SQUARE_SIZE_MM)

    print(f"\nKnight move: {from_square.to_notation()} -> {to_square.to_notation()}")
    print(f"Waypoints generated: {len(waypoints)}")
    for i, wp in enumerate(waypoints):
        print(f"  {i+1}. ({wp.x:.1f}, {wp.y:.1f}) mm - {wp.description}")

    # Create motor controller
    controller = create_test_controller()
    assert controller.electromagnet is not None

    # Execute the movement plan
    # 1. Move to pickup position with magnet OFF
    controller.electromagnet.off()
    positions, timestamps, speeds, magnet_states = capture_movement_path(
        controller, [movement_plan.pickup_position], sample_rate=20
    )

    # 2. Turn magnet ON to pick up the knight
    controller.electromagnet.on()

    # 3. Navigate through all waypoints with magnet ON
    for waypoint_step in movement_plan.waypoints:
        pos2, time2, speed2, mag2 = capture_movement_path(
            controller, [waypoint_step], sample_rate=20
        )
        positions.extend(pos2[1:])
        timestamps.extend([t + timestamps[-1] for t in time2[1:]])
        speeds.extend(speed2[1:])
        magnet_states.extend(mag2[1:])

    # Release piece at destination
    controller.electromagnet.off()

    # Convert positions back to mm for plotting
    path_x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    path_y_mm = [y / config.STEPS_PER_MM for _, y in positions]

    # Create visualization
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 18))

    # Row 1: Chess board with pieces showing obstacle
    setup_chess_board_plot(
        ax1,
        title=f"Knight Move: {from_square.to_notation()} → {to_square.to_notation()}\n"
        "Navigating Around Pawns",
        show_coordinates=True,
    )
    draw_chess_pieces(ax1, game)

    # Mark destination
    ax1.plot(
        to_square.col + 0.5,
        to_square.row + 0.5,
        "x",
        color="red",
        markersize=20,
        markeredgewidth=3,
        label="Destination",
        zorder=11,
    )
    ax1.legend()

    # Row 2: Movement path with waypoints
    setup_movement_plot(
        ax2, title="Magnet Path with Waypoints\n(Green=OFF, Red=ON)", show_capture_areas=True
    )
    draw_movement_path(ax2, path_x_mm, path_y_mm, magnet_states)

    # Mark waypoints
    waypoint_tuples = [(wp.x, wp.y, wp.description) for wp in waypoints]
    draw_waypoint_markers(ax2, waypoint_tuples)

    # Row 3: Speed profile
    setup_speed_plot(ax3, title="Movement Speed Profile")
    draw_speed_profile(ax3, timestamps, speeds)

    # Add overall title
    fig.suptitle(
        "Knight Pathfinding with Obstacle Avoidance",
        fontsize=14,
        fontweight="bold",
    )

    # Save
    output_path = OUTPUT_DIR / "knight_b1_c3_avoidance.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\nSaved visualization: {output_path}")
