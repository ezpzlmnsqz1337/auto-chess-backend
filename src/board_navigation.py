"""
Chess board navigation utilities.

Converts chess board coordinates (row, col) to motor step positions.
"""

import config


def square_to_steps(row: int, col: int) -> tuple[int, int]:
    """
    Convert chess board square coordinates to motor step positions.

    Assumes (0,0) is bottom-left square (a1 in chess notation).
    Returns the center position of the square.

    Args:
        row: Row number (0-7, where 0 is bottom)
        col: Column number (0-7, where 0 is leftmost)

    Returns:
        Tuple of (x_steps, y_steps) for the center of the square
    """
    if not (0 <= row < config.BOARD_ROWS):
        raise ValueError(f"Row {row} out of bounds (0-{config.BOARD_ROWS - 1})")
    if not (0 <= col < config.BOARD_COLS):
        raise ValueError(f"Column {col} out of bounds (0-{config.BOARD_COLS - 1})")

    # Calculate center of square in millimeters from origin
    center_x_mm = (col + 0.5) * config.SQUARE_SIZE_MM
    center_y_mm = (row + 0.5) * config.SQUARE_SIZE_MM

    # Convert to steps
    x_steps = int(center_x_mm * config.STEPS_PER_MM)
    y_steps = int(center_y_mm * config.STEPS_PER_MM)

    return (x_steps, y_steps)


def chess_notation_to_steps(notation: str) -> tuple[int, int]:
    """
    Convert chess notation (e.g., 'e4') to motor step positions.

    Args:
        notation: Chess notation like 'a1', 'e4', 'h8'

    Returns:
        Tuple of (x_steps, y_steps) for the center of the square
    """
    if len(notation) != 2:
        raise ValueError(f"Invalid chess notation: {notation}")

    col_char = notation[0].lower()
    row_char = notation[1]

    if not ("a" <= col_char <= "h"):
        raise ValueError(f"Invalid column: {col_char}")
    if not ("1" <= row_char <= "8"):
        raise ValueError(f"Invalid row: {row_char}")

    col = ord(col_char) - ord("a")  # a=0, b=1, ..., h=7
    row = int(row_char) - 1  # 1=0, 2=1, ..., 8=7

    return square_to_steps(row, col)


def steps_to_mm(x_steps: int, y_steps: int) -> tuple[float, float]:
    """
    Convert step positions to millimeters from origin.

    Args:
        x_steps: X position in steps
        y_steps: Y position in steps

    Returns:
        Tuple of (x_mm, y_mm)
    """
    x_mm = x_steps / config.STEPS_PER_MM
    y_mm = y_steps / config.STEPS_PER_MM
    return (x_mm, y_mm)


def get_board_dimensions_mm() -> tuple[float, float]:
    """Get the board dimensions in millimeters."""
    return (config.BOARD_COLS * config.SQUARE_SIZE_MM, config.BOARD_ROWS * config.SQUARE_SIZE_MM)


def get_board_dimensions_steps() -> tuple[int, int]:
    """Get the board dimensions in steps."""
    return (config.BOARD_WIDTH_STEPS, config.BOARD_HEIGHT_STEPS)
