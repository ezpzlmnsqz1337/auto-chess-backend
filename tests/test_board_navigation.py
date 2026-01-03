"""Chess board navigation tests with visualizations."""

from pathlib import Path

import matplotlib.pyplot as plt

import config
from demo_patterns import get_diagonal_patterns, get_edge_square_pattern, get_snake_pattern
from tests.test_utils import capture_movement_path, create_test_controller
from tests.visualization import (
    convert_steps_to_mm,
    draw_movement_path_gradient,
    draw_speed_profile,
    setup_movement_plot,
    setup_speed_plot,
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
    positions, timestamps, speeds, magnet_states = capture_movement_path(controller, corners)

    # Convert positions to mm for plotting
    x_mm, y_mm = convert_steps_to_mm(positions)

    # Create combined plot with path on top, speed on bottom
    fig = plt.figure(figsize=(12, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1], hspace=0.3)

    # Top: Path plot
    ax1 = fig.add_subplot(gs[0])
    setup_movement_plot(ax1, title="Board Edge Square Pattern")
    draw_movement_path_gradient(ax1, x_mm, y_mm)

    # Bottom: Speed analysis
    ax2 = fig.add_subplot(gs[1])
    setup_speed_plot(ax2, title="Motor Speed Analysis")
    draw_speed_profile(ax2, timestamps, speeds)

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
        positions, timestamps, speeds, magnet_states = capture_movement_path(
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
        x_mm, y_mm = convert_steps_to_mm(positions)

        setup_movement_plot(ax, title=f"{name} - Path")
        draw_movement_path_gradient(ax, x_mm, y_mm)

        # Start and end markers
        ax.plot(x_mm[0], y_mm[0], "go", markersize=10, label="Start", zorder=3)
        ax.plot(x_mm[-2], y_mm[-2], "ro", markersize=10, label="End", zorder=3)

        # Get unique legend entries
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles, strict=False))
        ax.legend(by_label.values(), by_label.keys(), fontsize=8, loc="upper right")

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
        setup_speed_plot(ax, title=f"{name} - Speed")
        draw_speed_profile(ax, timestamps, speeds)

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
    positions, timestamps, speeds, magnet_states = capture_movement_path(controller, target_positions)

    # Convert positions to mm for plotting
    x_mm, y_mm = convert_steps_to_mm(positions)

    # Create combined plot with path on top, speed on bottom
    fig = plt.figure(figsize=(12, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1], hspace=0.3)

    # Top: Path plot
    ax1 = fig.add_subplot(gs[0])
    setup_movement_plot(
        ax1, title=f"Snake Pattern - All {config.BOARD_ROWS * config.BOARD_COLS} Squares"
    )
    draw_movement_path_gradient(ax1, x_mm, y_mm)

    # Bottom: Speed analysis
    ax2 = fig.add_subplot(gs[1])
    setup_speed_plot(ax2, title="Motor Speed Analysis")
    draw_speed_profile(ax2, timestamps, speeds)

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
