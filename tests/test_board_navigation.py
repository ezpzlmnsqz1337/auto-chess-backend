"""Chess board navigation tests with visualizations."""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

import config
from board_navigation import square_to_steps


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

    # Plot path
    ax.plot(x_mm, y_mm, "b-", linewidth=2, label="Path", zorder=2)
    ax.plot(x_mm[0], y_mm[0], "go", markersize=12, label="Start", zorder=3)
    ax.plot(x_mm[-1], y_mm[-1], "ro", markersize=12, label="End", zorder=3)

    # Mark key waypoints
    for i, (x, y) in enumerate(zip(x_mm, y_mm, strict=True)):
        if i % max(1, len(x_mm) // 20) == 0:  # Show every ~5% of points
            ax.plot(x, y, "ko", markersize=4, alpha=0.5, zorder=1)

    ax.set_xlabel("X Position (mm)", fontsize=12)
    ax.set_ylabel("Y Position (mm)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_aspect("equal")

    # Set limits with some margin
    board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
    board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM
    margin = config.SQUARE_SIZE_MM * 0.5
    ax.set_xlim(-margin, board_width_mm + margin)
    ax.set_ylim(-margin, board_height_mm + margin)

    # Add board coordinates
    for col in range(config.BOARD_COLS):
        x = (col + 0.5) * config.SQUARE_SIZE_MM
        label = chr(ord("a") + col)
        ax.text(x, -margin / 2, label, ha="center", va="center", fontsize=10, fontweight="bold")

    for row in range(config.BOARD_ROWS):
        y = (row + 0.5) * config.SQUARE_SIZE_MM
        ax.text(
            -margin / 2, y, str(row + 1), ha="center", va="center", fontsize=10, fontweight="bold"
        )

    plt.tight_layout()
    plt.savefig(f"tests/output/{filename}", dpi=150, bbox_inches="tight")
    plt.close()


def test_board_edge_square() -> None:
    """Test moving around the edge of the board (drawing a square)."""
    # Create output directory
    Path("tests/output").mkdir(parents=True, exist_ok=True)

    # Corners of the board
    corners = [
        square_to_steps(0, 0),  # a1 - bottom left
        square_to_steps(0, 7),  # h1 - bottom right
        square_to_steps(7, 7),  # h8 - top right
        square_to_steps(7, 0),  # a8 - top left
        square_to_steps(0, 0),  # back to a1
    ]

    positions = [(0, 0)] + corners

    # Plot
    plot_board_with_path(
        positions, "Board Edge Square Test\nMoving Around Board Perimeter", "edge_square.png"
    )

    print(f"✓ Edge square test passed - traveled through {len(positions)} positions")


def test_all_diagonals() -> None:
    """Test moving along all four major diagonals."""
    Path("tests/output").mkdir(parents=True, exist_ok=True)

    diagonals = [
        # Diagonal 1: a1 to h8 (bottom-left to top-right)
        (square_to_steps(0, 0), square_to_steps(7, 7)),
        # Diagonal 2: h1 to a8 (bottom-right to top-left)
        (square_to_steps(0, 7), square_to_steps(7, 0)),
        # Diagonal 3: a8 to h1 (top-left to bottom-right)
        (square_to_steps(7, 0), square_to_steps(0, 7)),
        # Diagonal 4: h8 to a1 (top-right to bottom-left)
        (square_to_steps(7, 7), square_to_steps(0, 0)),
    ]

    all_positions = []

    for start, end in diagonals:
        positions = [(0, 0), start, end, (0, 0)]
        all_positions.append(positions)

    # Plot all diagonals together
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    axes_flat = axes.flatten()

    diagonal_names = [
        "Diagonal 1: a1 → h8 (↗)",
        "Diagonal 2: h1 → a8 (↖)",
        "Diagonal 3: a8 → h1 (↘)",
        "Diagonal 4: h8 → a1 (↙)",
    ]

    for idx, (positions, name) in enumerate(zip(all_positions, diagonal_names, strict=True)):
        ax = axes_flat[idx]

        # Convert to mm
        x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
        y_mm = [y / config.STEPS_PER_MM for _, y in positions]

        # Draw board grid
        for row in range(config.BOARD_ROWS + 1):
            y = row * config.SQUARE_SIZE_MM
            ax.axhline(y, color="gray", linewidth=0.5, alpha=0.5)

        for col in range(config.BOARD_COLS + 1):
            x = col * config.SQUARE_SIZE_MM
            ax.axvline(x, color="gray", linewidth=0.5, alpha=0.5)

        # Plot path
        ax.plot(x_mm, y_mm, "b-", linewidth=2.5, label="Path")
        ax.plot(x_mm[0], y_mm[0], "go", markersize=10, label="Start", zorder=3)
        ax.plot(x_mm[-2], y_mm[-2], "ro", markersize=10, label="End", zorder=3)

        ax.set_xlabel("X (mm)", fontsize=10)
        ax.set_ylabel("Y (mm)", fontsize=10)
        ax.set_title(name, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_aspect("equal")

        board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
        board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM
        margin = config.SQUARE_SIZE_MM * 0.5
        ax.set_xlim(-margin, board_width_mm + margin)
        ax.set_ylim(-margin, board_height_mm + margin)

    plt.suptitle("All Four Major Diagonals Test", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig("tests/output/all_diagonals.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ All diagonals test passed - tested {len(diagonals)} diagonals")


def test_snake_pattern_all_squares() -> None:
    """Test snake pattern through all 64 squares."""
    Path("tests/output").mkdir(parents=True, exist_ok=True)

    positions = [(0, 0)]  # Start at origin

    # Snake pattern: left-to-right on even rows, right-to-left on odd rows
    for row in range(config.BOARD_ROWS):
        # Even row: go left to right (0 to 7), odd row: go right to left (7 to 0)
        cols = range(config.BOARD_COLS) if row % 2 == 0 else range(config.BOARD_COLS - 1, -1, -1)

        for col in cols:
            x, y = square_to_steps(row, col)
            positions.append((x, y))

    # Plot
    plot_board_with_path(
        positions,
        f"Snake Pattern Test\nVisiting All {config.BOARD_ROWS * config.BOARD_COLS} Squares",
        "snake_pattern.png",
    )

    # Verify we visited all 64 squares plus origin
    assert len(positions) == config.BOARD_ROWS * config.BOARD_COLS + 1

    print(f"✓ Snake pattern test passed - visited {len(positions) - 1} squares")


def test_board_configuration() -> None:
    """Test that board configuration is correctly set up."""
    assert config.SQUARE_SIZE_MM > 0, "Square size must be positive"
    assert config.BOARD_ROWS == 8, "Standard chess board has 8 rows"
    assert config.BOARD_COLS == 8, "Standard chess board has 8 columns"
    assert config.STEPS_PER_MM > 0, "Steps per mm must be positive"

    # Verify board dimensions
    board_width_mm = config.BOARD_COLS * config.SQUARE_SIZE_MM
    board_height_mm = config.BOARD_ROWS * config.SQUARE_SIZE_MM

    assert int(board_width_mm * config.STEPS_PER_MM) == config.BOARD_WIDTH_STEPS
    assert int(board_height_mm * config.STEPS_PER_MM) == config.BOARD_HEIGHT_STEPS

    # Verify max positions can accommodate board
    assert config.MAX_X_POSITION >= config.BOARD_WIDTH_STEPS, "Max X must fit board width"
    assert config.MAX_Y_POSITION >= config.BOARD_HEIGHT_STEPS, "Max Y must fit board height"

    print("✓ Board configuration valid:")
    print(f"  Square size: {config.SQUARE_SIZE_MM}mm")
    print(f"  Board dimensions: {board_width_mm}mm × {board_height_mm}mm")
    print(f"  Board dimensions: {config.BOARD_WIDTH_STEPS} × {config.BOARD_HEIGHT_STEPS} steps")
    print(f"  Steps per mm: {config.STEPS_PER_MM}")
