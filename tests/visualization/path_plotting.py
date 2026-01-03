"""Path plotting utilities for movement visualizations."""

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

import config
from tests.visualization.board_drawing import (
    add_board_coordinates,
    draw_chess_board_grid,
    setup_board_axes,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes


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


def plot_path_with_magnet_state(
    ax: "Axes",
    x_mm: list[float],
    y_mm: list[float],
    magnet_states: list[bool],
) -> None:
    """
    Plot a path colored by magnet state (red = on, green = off).

    Args:
        ax: Matplotlib axes to plot on
        x_mm: X coordinates in millimeters
        y_mm: Y coordinates in millimeters
        magnet_states: Boolean list indicating if magnet was on at each point
    """
    if len(x_mm) < 2:
        return

    # Create segments for line collection
    points = np.array([x_mm, y_mm]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create colors based on magnet state (use state at start of each segment)
    colors = []
    for i in range(len(segments)):
        if magnet_states[i]:  # Magnet on
            colors.append((1.0, 0.0, 0.0, 0.8))  # Red with alpha
        else:  # Magnet off
            colors.append((0.0, 0.8, 0.0, 0.8))  # Green with alpha

    # Create and add LineCollection
    lc = LineCollection(segments, colors=colors, linewidth=2.5, zorder=2)  # type: ignore[arg-type]
    ax.add_collection(lc)

    # Add legend entries (create dummy lines for legend)
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', lw=2.5, label='Magnet ON'),
        Line2D([0], [0], color='green', lw=2.5, label='Magnet OFF')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)


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
