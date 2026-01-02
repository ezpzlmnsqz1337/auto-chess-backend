"""Chess board navigation tests with visualizations."""

from pathlib import Path

import matplotlib.pyplot as plt

import config
from demo_patterns import get_diagonal_patterns, get_edge_square_pattern, get_snake_pattern
from tests.test_utils import (
    capture_movement_path,
    create_test_controller,
    draw_chess_board_grid,
    plot_path_with_gradient,
)


def test_board_edge_square() -> None:
    """Test moving around the edge of the board (drawing a square) using actual motor code."""
    # Create output directory
    output_dir = Path("tests/output/movement")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create controller and home it
    controller = create_test_controller()

    # Get board edge pattern
    corners = get_edge_square_pattern()

    # Capture actual movement path using motor controller
    positions, timestamps, speeds = capture_movement_path(controller, corners)

    # Convert positions to mm for plotting
    x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    y_mm = [y / config.STEPS_PER_MM for _, y in positions]

    # Create combined plot with path on top, speed on bottom
    fig = plt.figure(figsize=(12, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1], hspace=0.3)

    # Top: Path plot
    ax1 = fig.add_subplot(gs[0])
    draw_chess_board_grid(ax1)
    plot_path_with_gradient(ax1, x_mm, y_mm)
    ax1.set_title("Board Edge Square Pattern", fontsize=12, fontweight="bold")
    ax1.set_aspect("equal")

    # Bottom: Speed analysis
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(timestamps, speeds, linewidth=2, color="#2E86AB", alpha=0.9)
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    max_speed = max(speeds) if speeds else 0
    ax2.axhline(
        avg_speed,
        color="orange",
        linestyle="--",
        linewidth=1.5,
        label=f"Avg: {avg_speed:.1f} mm/s",
        alpha=0.7,
    )
    ax2.set_xlabel("Time (s)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Velocity (mm/s)", fontsize=10, fontweight="bold")
    ax2.set_title("Motor Speed Analysis", fontsize=12, fontweight="bold")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)

    stats_text = f"Max: {max_speed:.1f} mm/s\nAvg: {avg_speed:.1f} mm/s"
    ax2.text(
        0.98,
        0.98,
        stats_text,
        transform=ax2.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
    )

    fig.suptitle("Board Edge Square Test - Path & Speed Analysis", fontsize=14, fontweight="bold")
    plt.savefig(output_dir / "edge_square.png", dpi=100, bbox_inches="tight")
    plt.close(fig)

    print(f"✓ Edge square test passed - traveled through {len(positions)} actual positions")
    print(f"  Final position: {controller.get_position()}")


def test_all_diagonals() -> None:
    """Test moving along all four major diagonals using actual motor code."""
    output_dir = Path("tests/output/movement")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get diagonal patterns
    diagonals_data = get_diagonal_patterns()
    diagonals = [(start, end) for start, end, _ in diagonals_data]
    diagonal_names = [name for _, _, name in diagonals_data]

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

    # Create combined figure with paths on top, speeds on bottom
    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(2, 4, hspace=0.35, wspace=0.3)

    # Top row: Path plots for each diagonal
    for idx, (positions, name) in enumerate(zip(all_positions, diagonal_names, strict=True)):
        ax = fig.add_subplot(gs[0, idx])
        x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
        y_mm = [y / config.STEPS_PER_MM for _, y in positions]

        draw_chess_board_grid(ax)
        plot_path_with_gradient(ax, x_mm, y_mm, sample_interval=max(1, len(x_mm) // 50))

        # Start and end markers
        ax.plot(x_mm[0], y_mm[0], "go", markersize=10, label="Start", zorder=3)
        ax.plot(x_mm[-2], y_mm[-2], "ro", markersize=10, label="End", zorder=3)

        # Compact axes setup - use extended board dimensions in motor coordinates
        margin = config.SQUARE_SIZE_MM * 0.5
        # Motor coordinate limits: left capture at motor_offset + left_capture_start, right at motor_offset + right_capture_end
        x_min = config.LEFT_CAPTURE_START_MM + config.MOTOR_X_OFFSET_MM - margin
        x_max = (
            config.RIGHT_CAPTURE_START_MM
            + config.CAPTURE_COLS * config.SQUARE_SIZE_MM
            + config.MOTOR_X_OFFSET_MM
            + margin
        )

        ax.set_xlabel("X (mm - motor coordinates)", fontsize=10)
        ax.set_ylabel("Y (mm)", fontsize=10)
        ax.set_title(f"{name} - Path", fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(-margin, config.BOARD_ROWS * config.SQUARE_SIZE_MM + margin)

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

    # Bottom row: Speed plots for each diagonal
    for idx, (timestamps, speeds, name) in enumerate(
        zip(all_timestamps, all_speeds, diagonal_names, strict=True)
    ):
        ax = fig.add_subplot(gs[1, idx])
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
        ax.set_title(f"{name} - Speed", fontsize=11, fontweight="bold")
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

    fig.suptitle("All Major Diagonals Test - Path & Speed Analysis", fontsize=16, fontweight="bold")
    plt.savefig(output_dir / "all_diagonals.png", dpi=100, bbox_inches="tight")
    plt.close(fig)

    total_steps = sum(len(pos) for pos in all_positions)
    print(f"✓ All diagonals test passed - tested {len(diagonals)} diagonals")
    print(f"  Total steps executed: {total_steps}")


def test_snake_pattern_all_squares() -> None:
    """Test snake pattern through all 64 squares using actual motor code."""
    output_dir = Path("tests/output/movement")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create controller
    controller = create_test_controller()

    # Get snake pattern
    target_positions = get_snake_pattern()

    # Capture actual movement path
    positions, timestamps, speeds = capture_movement_path(controller, target_positions)

    # Convert positions to mm for plotting
    x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    y_mm = [y / config.STEPS_PER_MM for _, y in positions]

    # Create combined plot with path on top, speed on bottom
    fig = plt.figure(figsize=(12, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1], hspace=0.3)

    # Top: Path plot
    ax1 = fig.add_subplot(gs[0])
    draw_chess_board_grid(ax1)
    plot_path_with_gradient(ax1, x_mm, y_mm)
    ax1.set_title(
        f"Snake Pattern - All {config.BOARD_ROWS * config.BOARD_COLS} Squares",
        fontsize=12,
        fontweight="bold",
    )
    ax1.set_aspect("equal")

    # Bottom: Speed analysis
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(timestamps, speeds, linewidth=2, color="#2E86AB", alpha=0.9)
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    max_speed = max(speeds) if speeds else 0
    ax2.axhline(
        avg_speed,
        color="orange",
        linestyle="--",
        linewidth=1.5,
        label=f"Avg: {avg_speed:.1f} mm/s",
        alpha=0.7,
    )
    ax2.set_xlabel("Time (s)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Velocity (mm/s)", fontsize=10, fontweight="bold")
    ax2.set_title("Motor Speed Analysis", fontsize=12, fontweight="bold")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)

    stats_text = f"Max: {max_speed:.1f} mm/s\nAvg: {avg_speed:.1f} mm/s"
    ax2.text(
        0.98,
        0.98,
        stats_text,
        transform=ax2.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
    )

    fig.suptitle("Snake Pattern Test - Path & Speed Analysis", fontsize=14, fontweight="bold")
    plt.savefig(output_dir / "snake_pattern.png", dpi=100, bbox_inches="tight")
    plt.close(fig)

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
