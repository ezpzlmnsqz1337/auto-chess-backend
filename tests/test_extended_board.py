"""Tests for extended board navigation with capture areas."""

import pytest

import config
from board_navigation import extended_square_to_steps


def test_left_capture_area() -> None:
    """Test coordinate conversion for left capture area (black's captures)."""
    # Left capture area uses negative columns (-2, -1)
    x_steps, y_steps = extended_square_to_steps(row=0, col=-2)

    # Motor coordinates should be positive (left capture is after motor offset)
    assert x_steps > 0, "Motor coordinates must be positive"

    # Should be less than the main board's position
    main_x, _ = extended_square_to_steps(row=0, col=0)
    assert x_steps < main_x, "Left capture should be left of main board"

    # Row 0 should be at the bottom
    assert y_steps > 0, "Row 0 should be above origin"


def test_main_board_coordinates() -> None:
    """Test that main board coordinates work correctly with motor offset."""
    # a1 (bottom-left of main board)
    x_steps, y_steps = extended_square_to_steps(row=0, col=0)

    # a1 should be at motor position = offset + half square
    expected_x = int((config.MOTOR_X_OFFSET_MM + 0.5 * config.SQUARE_SIZE_MM) * config.STEPS_PER_MM)
    expected_y = int(0.5 * config.SQUARE_SIZE_MM * config.STEPS_PER_MM)

    assert x_steps == expected_x, f"Expected {expected_x}, got {x_steps}"
    assert y_steps == expected_y


def test_right_capture_area() -> None:
    """Test coordinate conversion for right capture area (white's captures)."""
    # Right capture area uses columns 8, 9
    x_steps, y_steps = extended_square_to_steps(row=0, col=8)

    # Should be right of the main board (beyond column 7)
    main_board_end = int(8 * config.SQUARE_SIZE_MM * config.STEPS_PER_MM)
    assert x_steps > main_board_end, "Right capture area should be beyond main board"


def test_invalid_coordinates() -> None:
    """Test that invalid coordinates raise appropriate errors."""
    # Column too far left
    with pytest.raises(ValueError, match="Column .* out of bounds"):
        extended_square_to_steps(row=0, col=-3)

    # Column too far right
    with pytest.raises(ValueError, match="Column .* out of bounds"):
        extended_square_to_steps(row=0, col=10)

    # Row too high
    with pytest.raises(ValueError, match="Row .* out of bounds"):
        extended_square_to_steps(row=8, col=0)

    # Row negative
    with pytest.raises(ValueError, match="Row .* out of bounds"):
        extended_square_to_steps(row=-1, col=0)


def test_capture_area_offset() -> None:
    """Test that capture areas are offset by 24mm from main board."""
    # Get coordinates for rightmost main board square (column 7)
    x_main, _ = extended_square_to_steps(row=0, col=7)

    # Get coordinates for leftmost right capture square (column 8)
    x_capture, _ = extended_square_to_steps(row=0, col=8)

    # Calculate gap in millimeters
    gap_steps = x_capture - x_main - int(config.SQUARE_SIZE_MM * config.STEPS_PER_MM)
    gap_mm = gap_steps / config.STEPS_PER_MM

    # Should be approximately 24mm (allowing for rounding)
    assert abs(gap_mm - config.CAPTURE_OFFSET_MM) < 1.0, (
        f"Capture offset should be ~24mm, got {gap_mm}mm"
    )


def test_all_extended_board_squares() -> None:
    """Test that all 96 squares (2×8 + 8×8 + 2×8) have valid coordinates."""
    valid_count = 0

    # Left capture area: columns -2, -1
    for row in range(config.BOARD_ROWS):
        for col in range(-config.CAPTURE_COLS, 0):
            x, y = extended_square_to_steps(row, col)
            assert isinstance(x, int) and isinstance(y, int)
            valid_count += 1

    # Main board: columns 0-7
    for row in range(config.BOARD_ROWS):
        for col in range(config.BOARD_COLS):
            x, y = extended_square_to_steps(row, col)
            assert isinstance(x, int) and isinstance(y, int)
            valid_count += 1

    # Right capture area: columns 8, 9
    for row in range(config.BOARD_ROWS):
        for col in range(config.BOARD_COLS, config.BOARD_COLS + config.CAPTURE_COLS):
            x, y = extended_square_to_steps(row, col)
            assert isinstance(x, int) and isinstance(y, int)
            valid_count += 1

    assert valid_count == 96, f"Expected 96 squares, validated {valid_count}"
