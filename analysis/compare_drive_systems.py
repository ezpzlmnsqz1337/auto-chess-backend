"""Compare leadscrew vs GT2 belt drive system performance."""

import matplotlib.pyplot as plt
import numpy as np

# Configuration options
configs = {
    "Leadscrew (Current)": {
        "steps_per_mm": 160.0,
        "max_steps_per_sec": 1250,
        "min_delay": 0.0008,
        "color": "#e74c3c",
    },
    "GT2 Belt (Conservative)": {
        "steps_per_mm": 80.0,
        "max_steps_per_sec": 2000,
        "min_delay": 0.0005,
        "color": "#3498db",
    },
    "GT2 Belt (Marlin 60mm/s)": {
        "steps_per_mm": 80.0,
        "max_steps_per_sec": 4800,  # 60 mm/s
        "min_delay": 0.000208,
        "color": "#2ecc71",
    },
    "GT2 Belt (Marlin 100mm/s)": {
        "steps_per_mm": 80.0,
        "max_steps_per_sec": 8000,  # 100 mm/s
        "min_delay": 0.000125,
        "color": "#9b59b6",
    },
}

# Constants
SQUARE_SIZE_MM = 31.0
BOARD_SIZE_MM = 248.0
DIAGONAL_DISTANCE_MM = BOARD_SIZE_MM * np.sqrt(2)

# Acceleration parameters
MAX_STEP_DELAY = 0.004
ACCELERATION_STEPS = 300


def calculate_metrics(config_name: str, config: dict) -> dict:
    """Calculate performance metrics for a drive system."""
    steps_per_mm = config["steps_per_mm"]
    max_steps_per_sec = config["max_steps_per_sec"]
    min_delay = config["min_delay"]

    # Speed calculations
    max_speed_mm_per_sec = max_steps_per_sec / steps_per_mm
    diagonal_speed = max_speed_mm_per_sec * np.sqrt(2)

    # Time calculations
    time_per_square = SQUARE_SIZE_MM / max_speed_mm_per_sec
    full_diagonal_time = DIAGONAL_DISTANCE_MM / diagonal_speed

    # Acceleration calculations
    accel_distance = ACCELERATION_STEPS / steps_per_mm
    accel_time = ACCELERATION_STEPS * (MAX_STEP_DELAY + min_delay) / 2

    return {
        "max_speed": max_speed_mm_per_sec,
        "diagonal_speed": diagonal_speed,
        "time_per_square": time_per_square,
        "full_diagonal_time": full_diagonal_time,
        "accel_distance": accel_distance,
        "accel_time": accel_time,
    }


def calculate_velocity_profile(config: dict, distance_mm: float) -> tuple[np.ndarray, np.ndarray]:
    """Calculate velocity over time for a move with acceleration."""
    steps_per_mm = config["steps_per_mm"]
    total_steps = int(distance_mm * steps_per_mm)
    min_delay = config["min_delay"]

    accel_steps = min(ACCELERATION_STEPS, total_steps // 2)

    times = []
    velocities = []
    current_time = 0.0

    # Acceleration phase
    for step in range(accel_steps):
        progress = step / ACCELERATION_STEPS
        delay = MAX_STEP_DELAY - progress * (MAX_STEP_DELAY - min_delay)
        velocity = (1 / delay) / steps_per_mm  # mm/s

        times.append(current_time)
        velocities.append(velocity)
        current_time += delay

    # Constant speed phase
    constant_steps = total_steps - 2 * accel_steps
    if constant_steps > 0:
        max_velocity = (1 / min_delay) / steps_per_mm
        for _ in range(constant_steps):
            times.append(current_time)
            velocities.append(max_velocity)
            current_time += min_delay

    # Deceleration phase
    for step in range(accel_steps):
        progress = step / ACCELERATION_STEPS
        delay = min_delay + progress * (MAX_STEP_DELAY - min_delay)
        velocity = (1 / delay) / steps_per_mm

        times.append(current_time)
        velocities.append(velocity)
        current_time += delay

    return np.array(times), np.array(velocities)


def plot_comparison():
    """Create comprehensive comparison plots."""
    # Calculate metrics for all configs
    metrics = {name: calculate_metrics(name, config) for name, config in configs.items()}

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Drive System Performance Comparison", fontsize=16, fontweight="bold")

    # 1. Speed comparison
    ax = axes[0, 0]
    names = list(metrics.keys())
    speeds = [metrics[name]["max_speed"] for name in names]
    diagonal_speeds = [metrics[name]["diagonal_speed"] for name in names]
    colors = [configs[name]["color"] for name in names]

    x = np.arange(len(names))
    width = 0.35

    ax.bar(x - width / 2, speeds, width, label="Single Axis", color=colors, alpha=0.8)
    ax.bar(
        x + width / 2, diagonal_speeds, width, label="Diagonal", color=colors, alpha=0.5, hatch="//"
    )

    ax.set_ylabel("Speed (mm/s)", fontweight="bold")
    ax.set_title("Maximum Speed Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # Add value labels
    for i, (speed, diag_speed) in enumerate(zip(speeds, diagonal_speeds, strict=True)):
        ax.text(i - width / 2, speed + 1, f"{speed:.1f}", ha="center", fontsize=9)
        ax.text(i + width / 2, diag_speed + 1, f"{diag_speed:.1f}", ha="center", fontsize=9)

    # 2. Time per square
    ax = axes[0, 1]
    times = [metrics[name]["time_per_square"] for name in names]
    bars = ax.barh(names, times, color=colors, alpha=0.8)

    ax.set_xlabel("Time (seconds)", fontweight="bold")
    ax.set_title(f"Time to Cross One Square ({SQUARE_SIZE_MM}mm)")
    ax.grid(axis="x", alpha=0.3)

    # Add value labels
    for bar, time in zip(bars, times, strict=True):
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height() / 2, f"{time:.2f}s", va="center")

    # 3. Full diagonal time
    ax = axes[1, 0]
    full_times = [metrics[name]["full_diagonal_time"] for name in names]
    bars = ax.barh(names, full_times, color=colors, alpha=0.8)

    ax.set_xlabel("Time (seconds)", fontweight="bold")
    ax.set_title(f"Full Board Diagonal ({DIAGONAL_DISTANCE_MM:.1f}mm)")
    ax.grid(axis="x", alpha=0.3)

    # Add value labels
    for bar, time in zip(bars, full_times, strict=True):
        width = bar.get_width()
        ax.text(width + 0.5, bar.get_y() + bar.get_height() / 2, f"{time:.1f}s", va="center")

    # 4. Velocity profile for one square move
    ax = axes[1, 1]
    for name, config in configs.items():
        times, velocities = calculate_velocity_profile(config, SQUARE_SIZE_MM)
        ax.plot(times, velocities, label=name, color=config["color"], linewidth=2)

    ax.set_xlabel("Time (seconds)", fontweight="bold")
    ax.set_ylabel("Velocity (mm/s)", fontweight="bold")
    ax.set_title(f"Velocity Profile (Single {SQUARE_SIZE_MM}mm Square)")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("tests/output/drive_system_comparison.png", dpi=150, bbox_inches="tight")
    print("✓ Saved: tests/output/drive_system_comparison.png")

    # Create detailed acceleration comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Acceleration Profile Comparison (Full Diagonal Move)", fontsize=14, fontweight="bold"
    )

    # Velocity vs time
    ax = axes[0]
    for name, config in configs.items():
        times, velocities = calculate_velocity_profile(config, DIAGONAL_DISTANCE_MM / np.sqrt(2))
        ax.plot(times, velocities, label=name, color=config["color"], linewidth=2)

    ax.set_xlabel("Time (seconds)", fontweight="bold")
    ax.set_ylabel("Velocity (mm/s)", fontweight="bold")
    ax.set_title("Velocity vs Time")
    ax.legend()
    ax.grid(alpha=0.3)

    # Distance vs time
    ax = axes[1]
    for name, config in configs.items():
        times, velocities = calculate_velocity_profile(config, DIAGONAL_DISTANCE_MM / np.sqrt(2))
        # Calculate distance by integrating velocity
        distances = np.zeros_like(times)
        for i in range(1, len(times)):
            dt = times[i] - times[i - 1]
            distances[i] = distances[i - 1] + velocities[i] * dt

        ax.plot(times, distances, label=name, color=config["color"], linewidth=2)

    ax.set_xlabel("Time (seconds)", fontweight="bold")
    ax.set_ylabel("Distance (mm)", fontweight="bold")
    ax.set_title("Distance vs Time")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.axhline(BOARD_SIZE_MM, color="red", linestyle="--", alpha=0.3, label="Board width")

    plt.tight_layout()
    plt.savefig("tests/output/acceleration_comparison.png", dpi=150, bbox_inches="tight")
    print("✓ Saved: tests/output/acceleration_comparison.png")

    plt.show()


def print_summary():
    """Print text summary of comparison."""
    print("\n" + "=" * 70)
    print("DRIVE SYSTEM PERFORMANCE COMPARISON")
    print("=" * 70)

    for name, config in configs.items():
        metrics = calculate_metrics(name, config)

        print(f"\n{name}:")
        print("  Configuration:")
        print(f"    - Steps/mm: {config['steps_per_mm']}")
        print(f"    - Max steps/s: {config['max_steps_per_sec']}")
        print("\n  Performance:")
        print(f"    - Max speed (single axis): {metrics['max_speed']:.2f} mm/s")
        print(f"    - Max speed (diagonal): {metrics['diagonal_speed']:.2f} mm/s")
        print(f"    - Time per square: {metrics['time_per_square']:.2f}s")
        print(f"    - Full diagonal: {metrics['full_diagonal_time']:.1f}s")
        print(f"    - Accel distance: {metrics['accel_distance']:.1f}mm")
        print(f"    - Accel time: {metrics['accel_time']:.2f}s")

    print("\n" + "=" * 70)
    print("SPEED IMPROVEMENTS:")
    print("=" * 70)

    leadscrew = calculate_metrics("Leadscrew (Current)", configs["Leadscrew (Current)"])
    gt2_std = calculate_metrics("GT2 Belt (Conservative)", configs["GT2 Belt (Conservative)"])
    gt2_60 = calculate_metrics("GT2 Belt (Marlin 60mm/s)", configs["GT2 Belt (Marlin 60mm/s)"])
    gt2_100 = calculate_metrics("GT2 Belt (Marlin 100mm/s)", configs["GT2 Belt (Marlin 100mm/s)"])

    print("\nGT2 Belt (Conservative) vs Leadscrew:")
    print(f"  - Speed improvement: {gt2_std['max_speed'] / leadscrew['max_speed']:.2f}x faster")
    print(f"  - Time reduction: {leadscrew['time_per_square'] / gt2_std['time_per_square']:.2f}x")
    print(
        f"  - Full diagonal: {leadscrew['full_diagonal_time']:.1f}s → {gt2_std['full_diagonal_time']:.1f}s "
        f"({leadscrew['full_diagonal_time'] - gt2_std['full_diagonal_time']:.1f}s saved)"
    )

    print("\nGT2 Belt (Marlin 60mm/s) vs Leadscrew:")
    print(f"  - Speed improvement: {gt2_60['max_speed'] / leadscrew['max_speed']:.2f}x faster")
    print(f"  - Time reduction: {leadscrew['time_per_square'] / gt2_60['time_per_square']:.2f}x")
    print(
        f"  - Full diagonal: {leadscrew['full_diagonal_time']:.1f}s → {gt2_60['full_diagonal_time']:.1f}s "
        f"({leadscrew['full_diagonal_time'] - gt2_60['full_diagonal_time']:.1f}s saved)"
    )

    print("\nGT2 Belt (Marlin 100mm/s) vs Leadscrew:")
    print(f"  - Speed improvement: {gt2_100['max_speed'] / leadscrew['max_speed']:.2f}x faster")
    print(f"  - Time reduction: {leadscrew['time_per_square'] / gt2_100['time_per_square']:.2f}x")
    print(
        f"  - Full diagonal: {leadscrew['full_diagonal_time']:.1f}s → {gt2_100['full_diagonal_time']:.1f}s "
        f"({leadscrew['full_diagonal_time'] - gt2_100['full_diagonal_time']:.1f}s saved)"
    )

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    print_summary()
    plot_comparison()
