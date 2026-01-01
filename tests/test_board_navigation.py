"""Chess board navigation tests with visualizations."""

from pathlib import Path

import matplotlib.pyplot as plt

import config
from board_navigation import square_to_steps
from tests.test_utils import (
    capture_movement_path,
    create_test_controller,
    draw_chess_board_grid,
    plot_board_with_path,
    plot_path_with_gradient,
    plot_speed_over_time,
)


def test_board_edge_square() -> None:
    """Test moving around the edge of the board (drawing a square) using actual motor code."""
    # Create output directory
    Path("tests/output").mkdir(parents=True, exist_ok=True)

    # Create controller and home it
    controller = create_test_controller()

    # Corners of the board
    corners = [
        square_to_steps(0, 0),  # a1 - bottom left
        square_to_steps(0, 7),  # h1 - bottom right
        square_to_steps(7, 7),  # h8 - top right
        square_to_steps(7, 0),  # a8 - top left
        square_to_steps(0, 0),  # back to a1
    ]

    # Capture actual movement path using motor controller
    positions, timestamps, speeds = capture_movement_path(controller, corners)

    # Plot path
    plot_board_with_path(
        positions, "Board Edge Square Test\nMoving Around Board Perimeter", "edge_square.png"
    )

    # Plot speed over time
    plot_speed_over_time(
        timestamps,
        speeds,
        "Motor Speed - Board Edge Square Test",
        "edge_square_speed.png",
    )

    print(f"✓ Edge square test passed - traveled through {len(positions)} actual positions")
    print(f"  Final position: {controller.get_position()}")


def test_all_diagonals() -> None:
    """Test moving along all four major diagonals using actual motor code."""
    Path("tests/output").mkdir(parents=True, exist_ok=True)

    diagonals = [
        # Diagonal 1: a1 to h8 (bottom-left to top-right)
        (square_to_steps(0, 0), square_to_steps(7, 7)),
        # Diagonal 2: h1 to a8 (bottom-right to top-left)
        (square_to_steps(0, 7), square_to_steps(7, 0)),
        # Diagonal 3: a8 to h1 (top-left to bottom-right)
        (square_to_steps(7, 0), square_to_steps(0, 7)),
        # Diagonal 4: h8 to a1 (top-right to bottom-left)
        (square_to_steps(7, 7), square_to_steps(0, 0)),
    ]

    diagonal_names = [
        "Diagonal 1: a1 → h8 (↗)",
        "Diagonal 2: h1 → a8 (↖)",
        "Diagonal 3: a8 → h1 (↘)",
        "Diagonal 4: h8 → a1 (↙)",
    ]

    # Reuse single controller for all diagonals
    controller = create_test_controller()

    # Capture paths for all diagonals
    all_positions = []
    all_timestamps = []
    all_speeds = []
    for start, end in diagonals:
        # Capture: position to start, then diagonal move
        # Skip velocity tracking for the positioning move (first move)
        start_x, start_y = start
        end_x, end_y = end
        positions, timestamps, speeds = capture_movement_path(
            controller, [(start_x, start_y), (end_x, end_y)], skip_first_move=True
        )
        all_positions.append(positions)
        all_timestamps.append(timestamps)
        all_speeds.append(speeds)

    # Create 2x2 subplot
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    axes_flat = axes.flatten()

    # Plot each diagonal
    for positions, name, ax in zip(all_positions, diagonal_names, axes_flat, strict=True):
        x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
        y_mm = [y / config.STEPS_PER_MM for _, y in positions]

        draw_chess_board_grid(ax)
        plot_path_with_gradient(ax, x_mm, y_mm, sample_interval=max(1, len(x_mm) // 50))

        # Start and end markers
        ax.plot(x_mm[0], y_mm[0], "go", markersize=10, label="Start", zorder=3)
        ax.plot(x_mm[-2], y_mm[-2], "ro", markersize=10, label="End", zorder=3)

        # Compact axes setup
        board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
        board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM
        margin = config.SQUARE_SIZE_MM * 0.5

        ax.set_xlabel("X (mm)", fontsize=10)
        ax.set_ylabel("Y (mm)", fontsize=10)
        ax.set_title(name, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(-margin, board_width_mm + margin)
        ax.set_ylim(-margin, board_height_mm + margin)

        # Add position count
        ax.text(
            0.02,
            0.98,
            f"{len(x_mm)} pts",
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
        )

    plt.suptitle(
        "All Four Major Diagonals Test (Actual Motor Movement)", fontsize=16, fontweight="bold"
    )
    plt.tight_layout()
    plt.savefig("tests/output/all_diagonals.png", dpi=100, bbox_inches="tight")
    plt.close()

    # Create speed plot for all diagonals
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes_flat = axes.flatten()

    for timestamps, speeds, name, ax in zip(
        all_timestamps, all_speeds, diagonal_names, axes_flat, strict=True
    ):
        # Simple line plot like in analysis folder
        ax.plot(timestamps, speeds, linewidth=2, color="#2E86AB", alpha=0.9)

        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        ax.axhline(
            avg_speed,
            color="orange",
            linestyle="--",
            linewidth=1.5,
            label=f"Avg: {avg_speed:.1f} mm/s",
            alpha=0.7,
        )

        ax.set_xlabel("Time (s)", fontsize=10, fontweight="bold")
        ax.set_ylabel("Velocity (mm/s)", fontsize=10, fontweight="bold")
        ax.set_title(name, fontsize=11, fontweight="bold")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)

        stats_text = f"Max: {max_speed:.1f} mm/s\nAvg: {avg_speed:.1f} mm/s"
        ax.text(
            0.98,
            0.98,
            stats_text,
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="top",
            horizontalalignment="right",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
        )

    plt.suptitle("Motor Velocity - All Diagonals Test", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig("tests/output/all_diagonals_speed.png", dpi=100, bbox_inches="tight")
    plt.close()

    total_steps = sum(len(pos) for pos in all_positions)
    print(f"✓ All diagonals test passed - tested {len(diagonals)} diagonals")
    print(f"  Total steps executed: {total_steps}")


def test_snake_pattern_all_squares() -> None:
    """Test snake pattern through all 64 squares using actual motor code."""
    Path("tests/output").mkdir(parents=True, exist_ok=True)

    # Create controller
    controller = create_test_controller()

    # Build target positions for snake pattern
    target_positions = []

    # Snake pattern: left-to-right on even rows, right-to-left on odd rows
    for row in range(config.BOARD_ROWS):
        # Even row: go left to right (0 to 7), odd row: go right to left (7 to 0)
        cols = range(config.BOARD_COLS) if row % 2 == 0 else range(config.BOARD_COLS - 1, -1, -1)

        for col in cols:
            x, y = square_to_steps(row, col)
            target_positions.append((x, y))

    # Capture actual movement path
    positions, timestamps, speeds = capture_movement_path(controller, target_positions)

    # Plot path
    plot_board_with_path(
        positions,
        f"Snake Pattern Test\nVisiting All {config.BOARD_ROWS * config.BOARD_COLS} Squares (Actual Motor Movement)",
        "snake_pattern.png",
    )

    # Plot speed over time
    plot_speed_over_time(
        timestamps, speeds, "Motor Speed - Snake Pattern Test", "snake_pattern_speed.png"
    )

    # Verify we visited all 64 squares
    assert len(target_positions) == config.BOARD_ROWS * config.BOARD_COLS

    print(f"✓ Snake pattern test passed - visited {len(target_positions)} squares")
    print(f"  Total motor steps executed: {len(positions)}")
    print(f"  Final position: {controller.get_position()}")


def test_board_configuration() -> None:
    """Test that board configuration is correctly set up."""
    assert config.SQUARE_SIZE_MM > 0, "Square size must be positive"
    assert config.BOARD_ROWS == 8, "Standard chess board has 8 rows"
    assert config.BOARD_COLS == 8, "Standard chess board has 8 columns"
    assert config.STEPS_PER_MM > 0, "Steps per mm must be positive"

    # Verify board dimensions
    board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
    board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM

    assert int(board_width_mm * config.STEPS_PER_MM) == config.BOARD_WIDTH_STEPS
    assert int(board_height_mm * config.STEPS_PER_MM) == config.BOARD_HEIGHT_STEPS

    # Verify max positions can accommodate board
    assert config.MAX_X_POSITION >= config.BOARD_WIDTH_STEPS, "Max X must fit board width"
    assert config.MAX_Y_POSITION >= config.BOARD_HEIGHT_STEPS, "Max Y must fit board height"

    print("✓ Board configuration valid:")
    print(f"  Square size: {config.SQUARE_SIZE_MM}mm")
    print(f"  Board dimensions: {board_width_mm}mm × {board_height_mm}mm")
    print(f"  Board dimensions: {config.BOARD_WIDTH_STEPS} × {config.BOARD_HEIGHT_STEPS} steps")
    print(f"  Steps per mm: {config.STEPS_PER_MM}")
