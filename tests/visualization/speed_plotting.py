"""Speed plotting utilities for movement analysis."""

from pathlib import Path

import matplotlib.pyplot as plt


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
