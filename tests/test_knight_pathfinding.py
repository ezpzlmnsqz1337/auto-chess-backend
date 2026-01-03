"""Test knight pathfinding with obstacle avoidance."""

from pathlib import Path

import matplotlib.pyplot as plt
import pytest

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
        print(f"  {i + 1}. ({wp.x:.1f}, {wp.y:.1f}) mm - {wp.description}")

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


@pytest.mark.parametrize(
    "from_notation,to_notation,description",
    [
        ("b1", "c3", "Up-Right (2 up, 1 right)"),
        ("g1", "f3", "Up-Left (2 up, 1 left)"),
        ("b8", "c6", "Down-Right (2 down, 1 right)"),
        ("g8", "f6", "Down-Left (2 down, 1 left)"),
        ("d4", "f5", "Right-Up (2 right, 1 up)"),
        ("d4", "b5", "Left-Up (2 left, 1 up)"),
        ("d4", "f3", "Right-Down (2 right, 1 down)"),
        ("d4", "b3", "Left-Down (2 left, 1 down)"),
    ],
)
def test_knight_pathfinding_all_directions(
    from_notation: str, to_notation: str, description: str
) -> None:
    """Test knight pathfinding in all 8 possible directions."""
    # Set up game with empty board
    game = ChessGame()
    game.board.clear()

    from_square = Square.from_notation(from_notation)
    to_square = Square.from_notation(to_notation)

    # Add knight at starting position
    game.board[from_square] = Piece(PieceType.KNIGHT, Player.WHITE)

    # Get movement plan
    movement_plan = plan_knight_movement(from_square, to_square, game)
    waypoints = calculate_knight_path(from_square, to_square, game, config.SQUARE_SIZE_MM)

    print(f"\n{description}: {from_notation} -> {to_notation}")
    print(f"  Waypoints: {len(waypoints)}")
    for i, wp in enumerate(waypoints):
        print(f"    {i + 1}. {wp.description}")

    # Verify we got the expected number of waypoints (always 3: corner, edge, center)
    assert len(waypoints) == 3, f"Expected 3 waypoints, got {len(waypoints)}"
    assert len(movement_plan.waypoints) == 3, "Movement plan should have 3 waypoints"

    # Verify first waypoint is in the starting square
    assert (
        from_square.col * config.SQUARE_SIZE_MM
        <= waypoints[0].x
        <= (from_square.col + 1) * config.SQUARE_SIZE_MM
    ), "First waypoint should be in starting square"
    assert (
        from_square.row * config.SQUARE_SIZE_MM
        <= waypoints[0].y
        <= (from_square.row + 1) * config.SQUARE_SIZE_MM
    ), "First waypoint should be in starting square"

    # Verify last waypoint is at center of destination square
    expected_dest_x = (to_square.col + 0.5) * config.SQUARE_SIZE_MM
    expected_dest_y = (to_square.row + 0.5) * config.SQUARE_SIZE_MM
    assert abs(waypoints[-1].x - expected_dest_x) < 0.1, "Last waypoint should be at destination"
    assert abs(waypoints[-1].y - expected_dest_y) < 0.1, "Last waypoint should be at destination"


def test_knight_visualization_comparison() -> None:
    """Visualize multiple knight moves in a comparison grid."""
    # Test cases: (from, to, obstacles)
    test_cases = [
        ("b1", "c3", [(1, 1), (1, 2)], "Up-Right with obstacles"),
        ("g1", "f3", [(1, 5), (1, 6)], "Up-Left with obstacles"),
        ("d4", "f5", [(3, 4), (4, 4)], "Right-Up with obstacles"),
        ("d4", "b3", [(3, 2), (2, 2)], "Left-Down with obstacles"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    for idx, (from_notation, to_notation, obstacle_positions, desc) in enumerate(test_cases):
        # Set up game
        game = ChessGame()
        game.board.clear()

        from_square = Square.from_notation(from_notation)
        to_square = Square.from_notation(to_notation)

        # Add knight
        game.board[from_square] = Piece(PieceType.KNIGHT, Player.WHITE)

        # Add obstacles
        for row, col in obstacle_positions:
            game.board[Square(row, col)] = Piece(PieceType.PAWN, Player.WHITE)

        # Calculate path
        waypoints = calculate_knight_path(from_square, to_square, game, config.SQUARE_SIZE_MM)

        # Chess board view
        ax_board = axes[idx]
        setup_chess_board_plot(
            ax_board, title=f"{desc}\n{from_notation} → {to_notation}", show_coordinates=True
        )
        draw_chess_pieces(ax_board, game)

        # Mark destination
        ax_board.plot(
            to_square.col + 0.5,
            to_square.row + 0.5,
            "x",
            color="red",
            markersize=15,
            markeredgewidth=2,
            zorder=11,
        )

        # Draw waypoint path
        waypoint_x = [wp.x / config.SQUARE_SIZE_MM for wp in waypoints]
        waypoint_y = [wp.y / config.SQUARE_SIZE_MM for wp in waypoints]
        ax_board.plot(
            waypoint_x,
            waypoint_y,
            "b--",
            linewidth=2,
            marker="o",
            markersize=6,
            alpha=0.7,
            zorder=10,
            label="Path",
        )
        ax_board.legend(fontsize=8)

        # Path diagram in second row
        ax_path = axes[idx + 4]
        ax_path.set_xlim(-1, 9)
        ax_path.set_ylim(-1, 9)
        ax_path.set_aspect("equal")
        ax_path.set_title(f"Waypoints: {len(waypoints)}", fontsize=10)
        ax_path.grid(True, alpha=0.3)

        # Draw simplified path
        ax_path.plot(waypoint_x, waypoint_y, "b-", linewidth=3, marker="o", markersize=8)
        for i, wp in enumerate(waypoints):
            ax_path.text(
                wp.x / config.SQUARE_SIZE_MM + 0.2,
                wp.y / config.SQUARE_SIZE_MM + 0.2,
                f"{i + 1}",
                fontsize=8,
            )

    fig.suptitle("Knight Pathfinding: All Directions Comparison", fontsize=16, fontweight="bold")
    plt.tight_layout()

    output_path = OUTPUT_DIR / "knight_all_directions.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\nSaved comparison visualization: {output_path}")
