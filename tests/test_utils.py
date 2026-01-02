"""Test utilities for motor controller testing and visualization.

This module re-exports utilities from organized submodules for backward compatibility.
"""

# Motor test fixtures
from tests.fixtures import capture_movement_path, create_test_controller, create_test_motor

# Visualization utilities
from tests.visualization import (
    add_board_coordinates,
    add_position_count_label,
    add_start_end_markers,
    draw_chess_board_grid,
    plot_board_with_path,
    plot_path_with_gradient,
    plot_speed_over_time,
    setup_board_axes,
)

__all__ = [
    # Fixtures
    "create_test_controller",
    "create_test_motor",
    "capture_movement_path",
    # Visualization
    "draw_chess_board_grid",
    "add_board_coordinates",
    "setup_board_axes",
    "plot_path_with_gradient",
    "add_start_end_markers",
    "add_position_count_label",
    "plot_board_with_path",
    "plot_speed_over_time",
]
