"""Standardized movement path plotting functions."""

from typing import TYPE_CHECKING

from matplotlib.collections import LineCollection

import config
from tests.visualization.board_drawing import draw_chess_board_grid
from tests.visualization.path_plotting import plot_path_with_magnet_state

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def setup_movement_plot(
    ax: "Axes",
    title: str | None = None,
    show_capture_areas: bool = True,
) -> None:
    """
    Set up a movement plot with standard styling for motor path visualization.

    Uses motor coordinates (mm) and shows the full board with capture areas.

    Args:
        ax: Matplotlib axes
        title: Optional title for the plot
        show_capture_areas: Whether to show capture areas (default: True)
    """
    draw_chess_board_grid(ax, show_capture_areas=show_capture_areas, use_motor_coordinates=True)

    if title:
        ax.set_title(title, fontsize=10)

    ax.set_xlabel("X Position (mm)")
    ax.set_ylabel("Y Position (mm)")
    ax.set_aspect("equal")


def draw_movement_path(
    ax: "Axes",
    path_x_mm: list[float],
    path_y_mm: list[float],
    magnet_states: list[bool],
) -> None:
    """
    Draw a movement path with magnet state coloring.

    Green = magnet OFF (repositioning)
    Red = magnet ON (carrying piece)

    Args:
        ax: Matplotlib axes (must be set up with movement plot already)
        path_x_mm: X coordinates in millimeters
        path_y_mm: Y coordinates in millimeters
        magnet_states: Boolean list indicating magnet state at each point
    """
    if path_x_mm and path_y_mm and magnet_states:
        plot_path_with_magnet_state(ax, path_x_mm, path_y_mm, magnet_states)


def draw_movement_path_gradient(
    ax: "Axes",
    path_x_mm: list[float],
    path_y_mm: list[float],
    timestamps: list[float] | None = None,
) -> None:
    """
    Draw a movement path with time-based gradient coloring.

    Color progresses from blue (start) to red (end) based on time progression.

    Args:
        ax: Matplotlib axes (must be set up with movement plot already)
        path_x_mm: X coordinates in millimeters
        path_y_mm: Y coordinates in millimeters
        timestamps: Optional time values for gradient (if None, uses sequential ordering)
    """
    if not path_x_mm or not path_y_mm:
        return

    import numpy as np

    # Create line segments
    points = np.array([path_x_mm, path_y_mm]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create gradient colors based on time progression
    if timestamps:
        # Normalize timestamps to 0-1 range
        t_min, t_max = min(timestamps), max(timestamps)
        t_range = t_max - t_min if t_max > t_min else 1.0
        norm_times = [(t - t_min) / t_range for t in timestamps[:-1]]
    else:
        # Use sequential ordering
        norm_times = [i / (len(path_x_mm) - 1) for i in range(len(path_x_mm) - 1)]

    # Create colors: blue -> cyan -> green -> yellow -> red
    colors = [(0.0, 0.5, 1.0 - 0.5 * t, 0.8) for t in norm_times]

    # Create and add line collection
    lc = LineCollection(segments, colors=colors, linewidths=2, zorder=10)  # type: ignore[arg-type]
    ax.add_collection(lc)

    # Add start and end markers
    ax.plot(path_x_mm[0], path_y_mm[0], "go", markersize=8, label="Start", zorder=15)
    ax.plot(path_x_mm[-1], path_y_mm[-1], "ro", markersize=8, label="End", zorder=15)
    ax.legend(loc="upper right", fontsize=8)


def draw_waypoint_markers(
    ax: "Axes",
    waypoints: list[tuple[float, float, str]],
    use_motor_coordinates: bool = True,
) -> None:
    """
    Draw waypoint markers on a movement plot.

    Args:
        ax: Matplotlib axes
        waypoints: List of (x_mm, y_mm, description) tuples in board coordinates
        use_motor_coordinates: If True, apply motor offset to coordinates (default: True)
    """
    offset = config.MOTOR_X_OFFSET_MM if use_motor_coordinates else 0.0

    for i, (x, y, _desc) in enumerate(waypoints):
        # All waypoints are blue circles with smaller size
        marker = "o"
        color = "blue"

        # Apply motor offset to x coordinate
        x_plot = x + offset

        ax.plot(x_plot, y, marker, color=color, markersize=5, zorder=20)
        ax.annotate(
            f"WP{i + 1}",
            (x_plot, y),
            xytext=(-5, 5),
            textcoords="offset points",
            fontsize=8,
            ha="right",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
        )


def convert_steps_to_mm(
    positions: list[tuple[int, int]],
) -> tuple[list[float], list[float]]:
    """
    Convert position list from steps to millimeters.

    Args:
        positions: List of (x_steps, y_steps) tuples

    Returns:
        Tuple of (x_mm_list, y_mm_list)
    """
    x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
    y_mm = [y / config.STEPS_PER_MM for _, y in positions]
    return x_mm, y_mm
