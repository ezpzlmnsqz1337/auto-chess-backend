"""Movement path capture utilities for testing."""

from unittest.mock import patch

import config
from motor import MotorController


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
        controller.motor_x._pulse_step = tracked_pulse_x  # type: ignore[method-assign]
        controller.motor_y._pulse_step = tracked_pulse_y  # type: ignore[method-assign]

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
            controller.motor_x._pulse_step = original_pulse_x  # type: ignore[method-assign]
            controller.motor_y._pulse_step = original_pulse_y  # type: ignore[method-assign]

    return path, timestamps, velocities
