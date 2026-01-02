"""Test utilities for motor controller testing and visualization."""

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

import config
from motor import MotorController, StepperMotor

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def create_test_controller() -> MotorController:
    """
    Create a motor controller for testing with mock GPIO.

    Returns:
        Configured MotorController ready for testing
    """
    motor_x = create_test_motor("X")
    motor_y = create_test_motor("Y")

    controller = MotorController(
        motor_x,
        motor_y,
        enable_acceleration=config.ENABLE_ACCELERATION,
        min_step_delay=config.MIN_STEP_DELAY,
        max_step_delay=config.MAX_STEP_DELAY,
        accel_steps=config.ACCELERATION_STEPS,
    )
    # Simulate homing
    controller.motor_x.is_homed = True
    controller.motor_y.is_homed = True
    return controller


def create_test_motor(
    axis: str = "X", max_position: int | None = None, **kwargs: Any
) -> StepperMotor:
    """
    Create a single motor for testing with mock GPIO.

    Args:
        axis: "X" or "Y" to select motor configuration
        max_position: Override max_position (useful for fast tests)
        **kwargs: Additional StepperMotor parameters to override

    Returns:
        Configured StepperMotor ready for testing
    """
    if axis.upper() == "X":
        defaults: dict[str, Any] = {
            "step_pin": config.MOTOR_X_STEP_PIN,
            "dir_pin": config.MOTOR_X_DIR_PIN,
            "home_pin": config.MOTOR_X_HOME_PIN,
            "enable_pin": config.MOTOR_X_ENABLE_PIN,
            "invert_direction": config.MOTOR_X_INVERT,
            "max_position": max_position or config.MAX_X_POSITION,
        }
    else:  # Y axis
        defaults = {
            "step_pin": config.MOTOR_Y_STEP_PIN,
            "dir_pin": config.MOTOR_Y_DIR_PIN,
            "home_pin": config.MOTOR_Y_HOME_PIN,
            "enable_pin": config.MOTOR_Y_ENABLE_PIN,
            "invert_direction": config.MOTOR_Y_INVERT,
            "max_position": max_position or config.MAX_Y_POSITION,
        }

    # Add common defaults
    defaults.update(
        {
            "step_delay": config.STEP_DELAY,
            "step_pulse_duration": config.STEP_PULSE_DURATION,
        }
    )

    # Override with any provided kwargs
    defaults.update(kwargs)

    return StepperMotor(**defaults)


def capture_movement_path(
    controller: MotorController,
    target_positions: list[tuple[int, int]],
    sample_rate: int = 10,
    skip_first_move: bool = False,
) -> tuple[list[tuple[int, int]], list[float], list[float]]:
    """
    Capture the actual path the motors take through all target positions.

    Uses mock time.sleep to run without delays while still using real movement logic.
    Captures intermediate positions during movement to show the actual path.

    Args:
        controller: Motor controller instance
        target_positions: List of (x, y) target positions in steps
        sample_rate: Capture position every N steps (default: 10)
        skip_first_move: If True, don't record velocities for the first move (positioning)

    Returns:
        Tuple of (positions, timestamps, velocities) where:
        - positions: List of all (x, y) positions visited
        - timestamps: Simulated time in seconds for each position
        - velocities: Velocity in mm/s at each captured point
    """
    path = [controller.get_position()]
    timestamps = [0.0]
    velocities = [0.0]
    step_counter = [0]
    simulated_time = [0.0]  # Track simulated time based on step delays
    last_pos = path[0]
    last_time = 0.0
    last_sampled_step = [-sample_rate]  # Track when we last sampled to prevent double-sampling

    # Store original _pulse_step methods
    original_pulse_x = controller.motor_x._pulse_step
    original_pulse_y = controller.motor_y._pulse_step

    def record_sample() -> None:
        """Record position and velocity sample (called once per sample interval)."""
        nonlocal last_pos, last_time
        pos = controller.get_position()
        path.append(pos)
        t = simulated_time[0]
        timestamps.append(t)
        # Calculate velocity from actual distance traveled / time elapsed
        dx = (pos[0] - last_pos[0]) / config.STEPS_PER_MM
        dy = (pos[1] - last_pos[1]) / config.STEPS_PER_MM
        distance = (dx**2 + dy**2) ** 0.5
        dt = t - last_time
        velocity = distance / dt if dt > 0 else 0.0
        velocities.append(velocity)
        last_pos = pos
        last_time = t

    def tracked_pulse_x() -> None:
        """Wrap X motor pulse to capture positions and calculate simulated time."""
        original_pulse_x()
        # Add the step delay to simulated time
        simulated_time[0] += controller.motor_x.step_delay + controller.motor_x.step_pulse_duration
        step_counter[0] += 1
        # Sample if we're at a new sample interval
        current_sample_interval = step_counter[0] // sample_rate
        last_sample_interval = last_sampled_step[0] // sample_rate
        if current_sample_interval > last_sample_interval:
            record_sample()
            last_sampled_step[0] = step_counter[0]

    def tracked_pulse_y() -> None:
        """Wrap Y motor pulse to capture positions and calculate simulated time."""
        original_pulse_y()
        # Add Y's delay too - motors step sequentially, not simultaneously
        simulated_time[0] += controller.motor_y.step_delay + controller.motor_y.step_pulse_duration
        step_counter[0] += 1
        # Sample if we're at a new sample interval
        current_sample_interval = step_counter[0] // sample_rate
        last_sample_interval = last_sampled_step[0] // sample_rate
        if current_sample_interval > last_sample_interval:
            record_sample()
            last_sampled_step[0] = step_counter[0]

    # Mock time.sleep in motor.stepper_motor module to make tests instant
    with patch("motor.stepper_motor.time.sleep"):
        # Replace _pulse_step methods with tracked versions
        controller.motor_x._pulse_step = tracked_pulse_x
        controller.motor_y._pulse_step = tracked_pulse_y

        try:
            # Move through all target positions (uses real coordinated movement code)
            for move_idx, (x, y) in enumerate(target_positions):
                controller.move_to(x, y)

                if skip_first_move and move_idx == 0:
                    # Clear ALL samples from positioning move
                    path.clear()
                    timestamps.clear()
                    velocities.clear()
                    # Reset simulated time to start fresh for the actual move
                    simulated_time[0] = 0.0
                    # Reset tracking for next move
                    pos = controller.get_position()
                    path.append(pos)
                    timestamps.append(0.0)
                    velocities.append(0.0)
                    last_pos = pos
                    last_time = 0.0
                    # Reset last_sampled_step to avoid skipping first sample of next move
                    last_sampled_step[0] = -sample_rate
                    continue

                # Always capture final position of this move
                pos = controller.get_position()
                path.append(pos)
                t = simulated_time[0]
                timestamps.append(t)
                # Set velocity to 0 at waypoints since we're at rest
                # (avoid artifacts from long intervals between last sample and waypoint)
                velocities.append(0.0)
                last_pos = pos
                last_time = t
        finally:
            # Restore original methods
            controller.motor_x._pulse_step = original_pulse_x
            controller.motor_y._pulse_step = original_pulse_y

    return path, timestamps, velocities


def plot_speed_over_time(
    timestamps: list[float],
    speeds: list[float],
    title: str,
    filename: str,
) -> None:
    """
    Plot motor speed over time.

    Args:
        timestamps: List of timestamps in seconds
        speeds: List of speeds in mm/s
        title: Plot title
        filename: Output filename (saved in tests/output/)
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot velocity over time with simple line chart (like analysis folder)
    ax.plot(timestamps, speeds, linewidth=2, color="#2E86AB", alpha=0.9)

    # Add statistics
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    max_speed = max(speeds) if speeds else 0
    ax.axhline(
        avg_speed,
        color="orange",
        linestyle="--",
        linewidth=1.5,
        label=f"Average: {avg_speed:.1f} mm/s",
        alpha=0.7,
    )

    ax.set_xlabel("Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Velocity (mm/s)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10)

    # Add text box with statistics
    stats_text = (
        f"Max: {max_speed:.1f} mm/s\nAvg: {avg_speed:.1f} mm/s\nDuration: {timestamps[-1]:.2f}s"
    )
    ax.text(
        0.98,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
    )

    plt.tight_layout()
    output_dir = Path("tests/output/movement")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / filename, dpi=100, bbox_inches="tight")
    plt.close()


def plot_path_with_gradient(
    ax: "Axes",
    x_mm: list[float],
    y_mm: list[float],
    show_sample_points: bool = True,
    sample_interval: int | None = None,
) -> None:
    """
    Plot a path with color gradient showing progression.

    Args:
        ax: Matplotlib axes to plot on
        x_mm: X coordinates in millimeters
        y_mm: Y coordinates in millimeters
        show_sample_points: Whether to show cyan sample points
        sample_interval: Interval for sampling points (auto-calculated if None)
    """
    # Use LineCollection for efficient gradient rendering (single draw call)
    points = np.array([x_mm, y_mm]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create color array
    colors = plt.cm.viridis(np.linspace(0, 1, len(segments)))  # type: ignore[attr-defined]

    # Create and add LineCollection (much faster than individual plots)
    lc = LineCollection(segments, colors=colors, linewidth=1.5, alpha=0.7, zorder=2)  # type: ignore[arg-type]
    ax.add_collection(lc)

    # Show sample of captured points (reduce density for speed)
    if show_sample_points:
        if sample_interval is None:
            sample_interval = max(1, len(x_mm) // 50)  # Reduced from 100
        sample_x = x_mm[::sample_interval]
        sample_y = y_mm[::sample_interval]
        ax.plot(sample_x, sample_y, "o", color="cyan", markersize=2, alpha=0.6, zorder=3)


def add_start_end_markers(
    ax: "Axes", x_mm: list[float], y_mm: list[float], end_offset: int = 1
) -> None:
    """
    Add start (green) and end (red) markers to a path.

    Args:
        ax: Matplotlib axes to plot on
        x_mm: X coordinates in millimeters
        y_mm: Y coordinates in millimeters
        end_offset: Offset from end for the end marker (default: 1 for last point)
    """
    ax.plot(x_mm[0], y_mm[0], "go", markersize=12, label="Start", zorder=4)
    ax.plot(x_mm[-end_offset], y_mm[-end_offset], "ro", markersize=12, label="End", zorder=4)


def add_position_count_label(ax: "Axes", num_positions: int) -> None:
    """
    Add a text box showing the number of captured positions.

    Args:
        ax: Matplotlib axes to add label to
        num_positions: Number of positions captured
    """
    ax.text(
        0.02,
        0.98,
        f"Captured: {num_positions} positions",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
    )


def draw_chess_board_grid(ax: "Axes") -> None:
    """
    Draw chess board grid with alternating shaded squares.

    Args:
        ax: Matplotlib axes to draw on
    """
    # Draw grid lines
    for row in range(config.BOARD_ROWS + 1):
        y = row * config.SQUARE_SIZE_MM
        ax.axhline(y, color="gray", linewidth=0.5, alpha=0.5)

    for col in range(config.BOARD_COLS + 1):
        x = col * config.SQUARE_SIZE_MM
        ax.axvline(x, color="gray", linewidth=0.5, alpha=0.5)

    # Shade squares like chess board
    for row in range(config.BOARD_ROWS):
        for col in range(config.BOARD_COLS):
            if (row + col) % 2 == 1:
                x_start = col * config.SQUARE_SIZE_MM
                y_start = row * config.SQUARE_SIZE_MM
                rect = mpatches.Rectangle(
                    (x_start, y_start),
                    config.SQUARE_SIZE_MM,
                    config.SQUARE_SIZE_MM,
                    facecolor="lightgray",
                    alpha=0.3,
                )
                ax.add_patch(rect)


def add_board_coordinates(ax: "Axes", margin: float) -> None:
    """
    Add chess board coordinate labels (a-h, 1-8).

    Args:
        ax: Matplotlib axes to add labels to
        margin: Margin size for label positioning
    """
    # Column labels (a-h)
    for col in range(config.BOARD_COLS):
        x = (col + 0.5) * config.SQUARE_SIZE_MM
        label = chr(ord("a") + col)
        ax.text(x, -margin / 2, label, ha="center", va="center", fontsize=10, fontweight="bold")

    # Row labels (1-8)
    for row in range(config.BOARD_ROWS):
        y = (row + 0.5) * config.SQUARE_SIZE_MM
        ax.text(
            -margin / 2, y, str(row + 1), ha="center", va="center", fontsize=10, fontweight="bold"
        )


def setup_board_axes(ax: "Axes", title: str) -> float:
    """
    Configure axes for chess board visualization.

    Args:
        ax: Matplotlib axes to configure
        title: Title for the plot

    Returns:
        Margin size calculated for the board
    """
    board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
    board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM
    margin = config.SQUARE_SIZE_MM * 0.5

    ax.set_xlabel("X Position (mm)", fontsize=12)
    ax.set_ylabel("Y Position (mm)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_aspect("equal")
    ax.set_xlim(-margin, board_width_mm + margin)
    ax.set_ylim(-margin, board_height_mm + margin)

    return float(margin)


def plot_board_with_path(
    positions: list[tuple[int, int]], title: str, filename: str, show_squares: bool = True
) -> None:
    """
    Plot the chess board with a movement path.

    Args:
        positions: List of (x, y) tuples in steps
        title: Plot title
        filename: Output filename
        show_squares: Whether to show square grid
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # Convert positions to mm for better visualization
    x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    y_mm = [y / config.STEPS_PER_MM for _, y in positions]

    # Draw board grid
    if show_squares:
        draw_chess_board_grid(ax)

    # Plot path with gradient and sample points
    plot_path_with_gradient(ax, x_mm, y_mm)

    # Add markers and labels
    add_start_end_markers(ax, x_mm, y_mm)
    add_position_count_label(ax, len(positions))

    # Setup axes and add coordinates
    margin = setup_board_axes(ax, title)
    add_board_coordinates(ax, margin)

    plt.tight_layout()
    output_dir = Path("tests/output/movement")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / filename, dpi=100, bbox_inches="tight")
    plt.close()
