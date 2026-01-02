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

    # Convert to steps and apply motor offset
    # Motor homes at left edge, so we add offset to reach board positions
    x_steps = int((center_x_mm + config.MOTOR_X_OFFSET_MM) * config.STEPS_PER_MM)
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
    Convert motor step positions to board coordinate millimeters from origin (a1).

    Args:
        x_steps: X motor position in steps
        y_steps: Y motor position in steps

    Returns:
        Tuple of (x_mm, y_mm) in board coordinates (where a1 is at 0,0)
    """
    # Convert steps to mm and subtract motor offset to get board coordinates
    x_mm = (x_steps / config.STEPS_PER_MM) - config.MOTOR_X_OFFSET_MM
    y_mm = y_steps / config.STEPS_PER_MM
    return (x_mm, y_mm)


def get_board_dimensions_mm() -> tuple[float, float]:
    """Get the board dimensions in millimeters."""
    return (config.BOARD_COLS * config.SQUARE_SIZE_MM, config.BOARD_ROWS * config.SQUARE_SIZE_MM)


def get_board_dimensions_steps() -> tuple[int, int]:
    """Get the board dimensions in steps."""
    return (config.BOARD_WIDTH_STEPS, config.BOARD_HEIGHT_STEPS)


def extended_square_to_steps(row: int, col: int) -> tuple[int, int]:
    """
    Convert extended board square coordinates (including capture areas) to motor steps.

    Coordinate system:
    - Columns -2, -1: Left capture area (black's captured pieces)
    - Columns 0-7: Main chess board (a1 to h8)
    - Columns 8, 9: Right capture area (white's captured pieces)
    - Rows 0-7: Same as main board

    Args:
        row: Row number (0-7, where 0 is bottom)
        col: Column number (-2 to 9, where negative is left capture, 8-9 is right capture)

    Returns:
        Tuple of (x_steps, y_steps) for the center of the square
    """
    if not (0 <= row < config.BOARD_ROWS):
        raise ValueError(f"Row {row} out of bounds (0-{config.BOARD_ROWS - 1})")
    if not (-config.CAPTURE_COLS <= col < config.BOARD_COLS + config.CAPTURE_COLS):
        raise ValueError(
            f"Column {col} out of bounds ({-config.CAPTURE_COLS} to {config.BOARD_COLS + config.CAPTURE_COLS - 1})"
        )

    # Calculate center of square in millimeters from origin (a1)
    if col < 0:
        # Left capture area (negative columns)
        center_x_mm = (
            config.LEFT_CAPTURE_START_MM + (col + config.CAPTURE_COLS + 0.5) * config.SQUARE_SIZE_MM
        )
    elif col < config.BOARD_COLS:
        # Main board (columns 0-7)
        center_x_mm = (col + 0.5) * config.SQUARE_SIZE_MM
    else:
        # Right capture area (columns 8-9)
        center_x_mm = (
            config.RIGHT_CAPTURE_START_MM + (col - config.BOARD_COLS + 0.5) * config.SQUARE_SIZE_MM
        )

    center_y_mm = (row + 0.5) * config.SQUARE_SIZE_MM

    # Convert to steps and apply motor offset
    # Motor homes at left edge, so board coordinates are offset right in motor space
    x_steps = int((center_x_mm + config.MOTOR_X_OFFSET_MM) * config.STEPS_PER_MM)
    y_steps = int(center_y_mm * config.STEPS_PER_MM)

    return (x_steps, y_steps)


def get_extended_board_dimensions_mm() -> tuple[float, float]:
    """Get the extended board dimensions (including capture areas) in millimeters."""
    return (config.TOTAL_WIDTH_MM, config.TOTAL_HEIGHT_MM)


def get_extended_board_dimensions_steps() -> tuple[int, int]:
    """Get the extended board dimensions (including capture areas) in steps."""
    return (config.TOTAL_WIDTH_STEPS, config.TOTAL_HEIGHT_STEPS)
