"""Visualization utilities for test outputs."""

from tests.visualization.board_drawing import (
    add_board_coordinates,
    draw_chess_board_grid,
    draw_chess_pieces,
    setup_board_axes,
)
from tests.visualization.path_plotting import (
    add_position_count_label,
    add_start_end_markers,
    plot_board_with_path,
    plot_path_with_gradient,
    plot_path_with_magnet_state,
)
from tests.visualization.speed_plotting import plot_speed_over_time
from tests.visualization.standard_plots import (
    convert_steps_to_mm,
    draw_led_state,
    draw_movement_path,
    draw_movement_path_gradient,
    draw_reed_switch_state,
    draw_speed_profile,
    draw_waypoint_markers,
    setup_chess_board_plot,
    setup_led_board_plot,
    setup_movement_plot,
    setup_reed_switch_plot,
    setup_speed_plot,
)
from tests.visualization.standard_plots import (
    draw_chess_pieces as standard_draw_chess_pieces,
)

__all__ = [
    "draw_chess_board_grid",
    "add_board_coordinates",
    "setup_board_axes",
    "draw_chess_pieces",
    "plot_path_with_gradient",
    "plot_path_with_magnet_state",
    "add_start_end_markers",
    "add_position_count_label",
    "plot_board_with_path",
    "plot_speed_over_time",
    "setup_chess_board_plot",
    "setup_movement_plot",
    "draw_movement_path",
    "draw_movement_path_gradient",
    "setup_speed_plot",
    "draw_speed_profile",
    "draw_waypoint_markers",
    "convert_steps_to_mm",
    "standard_draw_chess_pieces",
    "setup_led_board_plot",
    "draw_led_state",
    "setup_reed_switch_plot",
    "draw_reed_switch_state",
]
