"""Capture management for placing captured pieces in capture areas."""

from dataclasses import dataclass

import config
from chess_game import Piece, PieceType, Player


@dataclass
class CaptureAreaPlacement:
    """Information about where to place a captured piece."""

    row: int  # Extended board row (-2 to 9)
    col: int  # Extended board column (0-7 within capture area, or main board)
    led_index: int  # LED index for the placement square
    is_left_area: bool  # True if left capture area (black captures), False if right (white)


def get_next_capture_slot(
    captured_piece: Piece,
    occupied_capture_squares: set[tuple[int, int]],
) -> CaptureAreaPlacement:
    """
    Determine where to place a captured piece in the capture area.

    Capture areas use the same layout pattern as starting position:
    - Row 0 (rank 1): Rook, Knight, Bishop, Queen (left area) / King, Bishop, Knight, Rook (right)
    - Row 1 (rank 2): Pawns
    - Rows 2-7 (ranks 3-8): For additional captured pieces (overflow)

    Args:
        captured_piece: The piece that was captured
        occupied_capture_squares: Set of (row, col) tuples already occupied in capture areas

    Returns:
        CaptureAreaPlacement with position and LED information
    """
    # Determine which capture area based on piece color
    # Black pieces go to LEFT capture area (columns -2, -1)
    # White pieces go to RIGHT capture area (columns 8, 9)
    is_left_area = captured_piece.player == Player.BLACK

    # Define piece type priority order (matching starting position)
    piece_order = [
        PieceType.ROOK,
        PieceType.KNIGHT,
        PieceType.BISHOP,
        PieceType.QUEEN,
        PieceType.KING,
        PieceType.BISHOP,
        PieceType.KNIGHT,
        PieceType.ROOK,
    ]

    # Pawns go in row 1
    if captured_piece.piece_type == PieceType.PAWN:
        target_row = 1
        # Try columns left to right
        for col in range(config.CAPTURE_COLS):
            extended_col = -config.CAPTURE_COLS + col if is_left_area else config.BOARD_COLS + col

            if (target_row, extended_col) not in occupied_capture_squares:
                led_index = _get_capture_area_led_index(target_row, col, is_left_area)
                return CaptureAreaPlacement(
                    row=target_row,
                    col=extended_col,
                    led_index=led_index,
                    is_left_area=is_left_area,
                )
    else:
        # Other pieces go in row 0, following piece order
        target_row = 0
        # Find the appropriate column based on piece type
        # For left area (black): use first occurrence in piece_order
        # For right area (white): use last occurrence if symmetric piece
        if captured_piece.piece_type in piece_order:
            for col in range(config.CAPTURE_COLS):
                if is_left_area:
                    extended_col = -config.CAPTURE_COLS + col
                else:
                    extended_col = config.BOARD_COLS + col

                if (target_row, extended_col) not in occupied_capture_squares:
                    led_index = _get_capture_area_led_index(target_row, col, is_left_area)
                    return CaptureAreaPlacement(
                        row=target_row,
                        col=extended_col,
                        led_index=led_index,
                        is_left_area=is_left_area,
                    )

    # Overflow: if standard positions filled, use remaining rows
    for row in range(2, config.BOARD_ROWS):
        for col in range(config.CAPTURE_COLS):
            extended_col = -config.CAPTURE_COLS + col if is_left_area else config.BOARD_COLS + col

            if (row, extended_col) not in occupied_capture_squares:
                led_index = _get_capture_area_led_index(row, col, is_left_area)
                return CaptureAreaPlacement(
                    row=row,
                    col=extended_col,
                    led_index=led_index,
                    is_left_area=is_left_area,
                )

    raise RuntimeError("No available capture slots (this should not happen)")


def _get_capture_area_led_index(row: int, col: int, is_left_area: bool) -> int:
    """
    Get LED index for a capture area square.

    Left capture area: LEDs 0-15 (columns -2, -1)
    Right capture area: LEDs 80-95 (columns 8, 9)

    Args:
        row: Board row (0-7)
        col: Column within capture area (0-1)
        is_left_area: True for left capture area, False for right

    Returns:
        LED index (0-15 for left, 80-95 for right)
    """
    if is_left_area:
        # Left capture area: LEDs 0-15
        # Layout: row 0 col 0 = LED 0, row 0 col 1 = LED 1, etc.
        return row * config.CAPTURE_COLS + col
    else:
        # Right capture area: LEDs 80-95
        return 80 + row * config.CAPTURE_COLS + col


def get_available_capture_slots(
    player_captured: Player,
    occupied_capture_squares: set[tuple[int, int]],
) -> list[int]:
    """
    Get list of available LED indices in the capture area for visual feedback.

    Args:
        player_captured: Which player's piece was captured (determines area)
        occupied_capture_squares: Already occupied squares

    Returns:
        List of LED indices that are available
    """
    is_left_area = player_captured == Player.BLACK
    available_leds = []

    for row in range(config.BOARD_ROWS):
        for col in range(config.CAPTURE_COLS):
            extended_col = -config.CAPTURE_COLS + col if is_left_area else config.BOARD_COLS + col

            if (row, extended_col) not in occupied_capture_squares:
                led_index = _get_capture_area_led_index(row, col, is_left_area)
                available_leds.append(led_index)

    return available_leds
