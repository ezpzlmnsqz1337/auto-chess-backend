"""Standardized speed profile plotting functions."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def setup_speed_plot(
    ax: "Axes",
    title: str = "Movement Speed Profile",
) -> None:
    """
    Set up a speed profile plot with standard styling.

    Args:
        ax: Matplotlib axes
        title: Title for the plot
    """
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Speed (mm/s)")
    ax.grid(True, alpha=0.3)


def draw_speed_profile(
    ax: "Axes",
    timestamps: list[float],
    speeds: list[float],
) -> None:
    """
    Draw a speed profile with standard styling.

    Shows the speed over time with average speed line and max speed annotation.

    Args:
        ax: Matplotlib axes (must be set up with speed plot already)
        timestamps: Time values in seconds
        speeds: Speed values in mm/s
    """
    if not timestamps or not speeds:
        return

    # Plot speed profile
    ax.plot(timestamps, speeds, linewidth=2, color="#2E86AB", alpha=0.9)

    # Add average speed line
    avg_speed = sum(speeds) / len(speeds)
    ax.axhline(
        y=avg_speed,
        color="orange",
        linestyle="--",
        linewidth=1.5,
        label=f"Avg: {avg_speed:.0f} mm/s",
    )

    # Add max speed annotation
    max_speed = max(speeds)
    ax.text(
        0.98,
        0.95,
        f"Max: {max_speed:.0f} mm/s",
        transform=ax.transAxes,
        fontsize=9,
        va="top",
        ha="right",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
    )

    ax.legend(loc="upper left", fontsize=8)
