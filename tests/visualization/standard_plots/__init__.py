"""Standardized plotting functions for consistent test visualizations."""

from .chess_plots import draw_chess_pieces, setup_chess_board_plot
from .led_plots import draw_led_state, setup_led_board_plot
from .movement_plots import (
    convert_steps_to_mm,
    draw_movement_path,
    draw_movement_path_gradient,
    draw_waypoint_markers,
    setup_movement_plot,
)
from .reed_switch_plots import draw_reed_switch_state, setup_reed_switch_plot
from .speed_plots import draw_speed_profile, setup_speed_plot

__all__ = [
    # Chess plots
    "setup_chess_board_plot",
    "draw_chess_pieces",
    # Movement plots
    "setup_movement_plot",
    "draw_movement_path",
    "draw_movement_path_gradient",
    "draw_waypoint_markers",
    "convert_steps_to_mm",
    # Speed plots
    "setup_speed_plot",
    "draw_speed_profile",
    # LED plots
    "setup_led_board_plot",
    "draw_led_state",
    # Reed switch plots
    "setup_reed_switch_plot",
    "draw_reed_switch_state",
]
