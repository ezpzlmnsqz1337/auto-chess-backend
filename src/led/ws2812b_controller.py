"""
WS2812B RGB LED strip controller for chess board visualization.

Controls 64 individually addressable RGB LEDs arranged in a grid, one per chess square.
LED indices map to chess squares starting from a1 (index 0) to h8 (index 63).

LED Index Mapping:
- Row 0 (White's back rank): a1=0, b1=1, c1=2, d1=3, e1=4, f1=5, g1=6, h1=7
- Row 1 (White's pawns):     a2=8, b2=9, c2=10, d2=11, e2=12, f2=13, g2=14, h2=15
- ...
- Row 7 (Black's back rank): a8=56, b8=57, c8=58, d8=59, e8=60, f8=61, g8=62, h8=63
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chess_game import ChessGame

try:
    from rpi_ws281x import PixelStrip

    HAS_WS281X = True
except ImportError:
    HAS_WS281X = False
    PixelStrip = None

from chess_game import Square
from config import (
    LED_BRIGHTNESS,
    LED_CHANNEL,
    LED_COUNT,
    LED_DATA_PIN,
    LED_DMA,
    LED_FREQ_HZ,
    LED_INVERT,
    LEDColors,
)


class MockPixelStrip:
    """Mock PixelStrip for testing without hardware."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.num_pixels: int = args[0] if args else kwargs.get("num", LED_COUNT)
        self.pixels: list[tuple[int, int, int]] = [(0, 0, 0)] * self.num_pixels
        self._brightness: int = LED_BRIGHTNESS

    def begin(self) -> None:
        """Initialize (no-op for mock)."""
        pass

    def setPixelColor(self, n: int, color: int) -> None:  # noqa: N802
        """Set pixel color (store in mock array)."""
        if 0 <= n < self.num_pixels:
            # Convert 24-bit int to RGB tuple
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            self.pixels[n] = (r, g, b)

    def setPixelColorRGB(self, n: int, r: int, g: int, b: int) -> None:  # noqa: N802
        """Set pixel color from RGB components."""
        if 0 <= n < self.num_pixels:
            self.pixels[n] = (r, g, b)

    def getPixelColor(self, n: int) -> int:  # noqa: N802
        """Get pixel color as 24-bit int."""
        if 0 <= n < self.num_pixels:
            r, g, b = self.pixels[n]
            return (r << 16) | (g << 8) | b
        return 0

    def getBrightness(self) -> int:  # noqa: N802
        """Get brightness."""
        return self._brightness

    def setBrightness(self, brightness: int) -> None:  # noqa: N802
        """Set brightness."""
        self._brightness = max(0, min(255, brightness))

    def show(self) -> None:
        """Update LEDs (no-op for mock)."""
        pass

    def numPixels(self) -> int:  # noqa: N802
        """Get number of pixels."""
        return self.num_pixels


class WS2812BController:
    """
    Controller for WS2812B RGB LED strip on chess board.

    Maps chess board squares to LED indices and provides methods for
    setting colors, patterns, and visual feedback during gameplay.
    """

    def __init__(self, use_mock: bool = False) -> None:
        """
        Initialize the LED controller.

        Args:
            use_mock: If True, use mock implementation instead of real hardware.
                     Automatically set to True if rpi_ws281x is not available.
        """
        self.use_mock = use_mock or not HAS_WS281X

        if self.use_mock:
            self.strip: MockPixelStrip | Any = MockPixelStrip(
                LED_COUNT,
                LED_DATA_PIN,
                LED_FREQ_HZ,
                LED_DMA,
                LED_INVERT,
                LED_BRIGHTNESS,
                LED_CHANNEL,
            )
        else:
            self.strip = PixelStrip(
                LED_COUNT,
                LED_DATA_PIN,
                LED_FREQ_HZ,
                LED_DMA,
                LED_INVERT,
                LED_BRIGHTNESS,
                LED_CHANNEL,
            )

        self.strip.begin()

    def square_to_led_index(self, square: Square) -> int:
        """
        Convert chess square to LED index.

        LED strip layout:
        - Starts at a1 (row=0, col=0) → index 0
        - Progresses left-to-right, bottom-to-top
        - Ends at h8 (row=7, col=7) → index 63

        Args:
            square: Chess square (row 0-7, col 0-7)

        Returns:
            LED index (0-63)
        """
        return square.row * 8 + square.col

    def led_index_to_square(self, index: int) -> Square:
        """
        Convert LED index to chess square.

        Args:
            index: LED index (0-63)

        Returns:
            Chess square

        Raises:
            ValueError: If index is out of range
        """
        if not 0 <= index < 64:
            raise ValueError(f"LED index {index} out of range (0-63)")

        row = index // 8
        col = index % 8
        return Square(row, col)

    def set_square_color(self, square: Square, color: tuple[int, int, int]) -> None:
        """
        Set the color of a specific chess square.

        Args:
            square: Chess square to illuminate
            color: RGB color tuple (0-255, 0-255, 0-255)
        """
        led_index = self.square_to_led_index(square)
        r, g, b = color
        self.strip.setPixelColorRGB(led_index, r, g, b)

    def get_square_color(self, square: Square) -> tuple[int, int, int]:
        """
        Get the current color of a chess square.

        Args:
            square: Chess square

        Returns:
            RGB color tuple (0-255, 0-255, 0-255)
        """
        led_index = self.square_to_led_index(square)
        color_int = self.strip.getPixelColor(led_index)
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return (r, g, b)

    def set_all_squares(self, color: tuple[int, int, int]) -> None:
        """
        Set all squares to the same color.

        Args:
            color: RGB color tuple (0-255, 0-255, 0-255)
        """
        r, g, b = color
        for i in range(64):
            self.strip.setPixelColorRGB(i, r, g, b)

    def clear_all(self) -> None:
        """Turn off all LEDs."""
        self.set_all_squares(LEDColors.OFF)

    def show(self) -> None:
        """Update the LED strip to display the current colors."""
        self.strip.show()

    def set_brightness(self, brightness: int) -> None:
        """
        Set global brightness.

        Args:
            brightness: Brightness level (0-255)
        """
        brightness = max(0, min(255, brightness))
        self.strip.setBrightness(brightness)

    def get_brightness(self) -> int:
        """Get current brightness level (0-255)."""
        return int(self.strip.getBrightness())

    def highlight_squares(
        self, squares: list[Square], color: tuple[int, int, int], clear_first: bool = False
    ) -> None:
        """
        Highlight multiple squares with the same color.

        Args:
            squares: List of chess squares to highlight
            color: RGB color tuple
            clear_first: If True, clear all LEDs before highlighting
        """
        if clear_first:
            self.clear_all()

        for square in squares:
            self.set_square_color(square, color)

    def show_valid_moves(
        self,
        from_square: Square,
        valid_moves: list[Square],
        capture_squares: list[Square] | None = None,
    ) -> None:
        """
        Show valid moves for a selected piece.

        Args:
            from_square: Currently selected square (blue)
            valid_moves: List of valid move destinations (green)
            capture_squares: List of squares with capturable pieces (orange)
        """
        self.clear_all()
        self.set_square_color(from_square, LEDColors.SELECTED)

        for square in valid_moves:
            if capture_squares and square in capture_squares:
                self.set_square_color(square, LEDColors.VALID_CAPTURE)
            else:
                self.set_square_color(square, LEDColors.VALID_MOVE)

        self.show()

    def show_check_state(self, king_square: Square) -> None:
        """
        Flash the king's square to indicate check.

        Args:
            king_square: Square containing the king in check
        """
        self.set_square_color(king_square, LEDColors.CHECK)
        self.show()

    def show_invalid_move_feedback(self, from_square: Square, to_square: Square) -> None:
        """
        Show red feedback for invalid move.

        Args:
            from_square: Starting square
            to_square: Invalid destination square
        """
        self.clear_all()
        self.set_square_color(from_square, LEDColors.INVALID_MOVE)
        self.set_square_color(to_square, LEDColors.INVALID_MOVE)
        self.show()

    def show_move_feedback(self, from_square: Square, to_square: Square) -> None:
        """
        Show dim feedback for the last move made.

        Args:
            from_square: Starting square
            to_square: Destination square
        """
        self.set_square_color(from_square, LEDColors.LAST_MOVE_FROM)
        self.set_square_color(to_square, LEDColors.LAST_MOVE_TO)
        self.show()

    def show_checkmate(self, king_square: Square) -> None:
        """
        Show bright red for checkmate.

        Args:
            king_square: Square containing the checkmated king
        """
        self.set_square_color(king_square, LEDColors.CHECKMATE)
        self.show()

    def show_stalemate(self) -> None:
        """Show yellow pattern for stalemate."""
        # Light up the four center squares
        center_squares = [
            Square(3, 3),
            Square(3, 4),
            Square(4, 3),
            Square(4, 4),
        ]
        self.clear_all()
        self.highlight_squares(center_squares, LEDColors.STALEMATE)
        self.show()

    def show_player_turn(self, game: "ChessGame") -> None:
        """
        Light up squares containing the active player's pieces.

        Args:
            game: ChessGame instance with current board state
        """
        from chess_game import Player

        color = (
            LEDColors.WHITE_PLAYER
            if game.current_player == Player.WHITE
            else LEDColors.BLACK_PLAYER
        )

        # Find all squares with pieces belonging to the current player
        player_squares = []
        for square, piece in game.board.items():
            if piece.player == game.current_player:
                player_squares.append(square)

        self.clear_all()
        self.highlight_squares(player_squares, color, clear_first=False)
        self.show()

    def rainbow_pattern(self, brightness_scale: float = 1.0) -> None:
        """
        Display a rainbow pattern across the board.

        Args:
            brightness_scale: Scale factor for brightness (0.0-1.0)
        """
        for i in range(64):
            # Create rainbow effect based on position
            hue = (i * 360) // 64
            r, g, b = self._hsv_to_rgb(hue, 1.0, brightness_scale)
            square = self.led_index_to_square(i)
            self.set_square_color(square, (r, g, b))
        self.show()

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> tuple[int, int, int]:
        """
        Convert HSV color to RGB.

        Args:
            h: Hue (0-360)
            s: Saturation (0.0-1.0)
            v: Value/brightness (0.0-1.0)

        Returns:
            RGB tuple (0-255, 0-255, 0-255)
        """
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if 0 <= h < 60:
            r_f, g_f, b_f = c, x, 0.0
        elif 60 <= h < 120:
            r_f, g_f, b_f = x, c, 0.0
        elif 120 <= h < 180:
            r_f, g_f, b_f = 0.0, c, x
        elif 180 <= h < 240:
            r_f, g_f, b_f = 0.0, x, c
        elif 240 <= h < 300:
            r_f, g_f, b_f = x, 0.0, c
        else:
            r_f, g_f, b_f = c, 0.0, x

        return (
            int((r_f + m) * 255),
            int((g_f + m) * 255),
            int((b_f + m) * 255),
        )

    def show_mode_selection(self, placed_squares: list[Square]) -> None:
        """
        Display interactive mode selection screen.

        Mode buttons on row 0 (white's back rank):
        - a1: Light blue button - Player vs AI with player as WHITE
        - b1: Blue button - Player vs AI with player as BLACK
        - d1: Yellow button - EASY difficulty (only when AI involved)
        - e1: Orange button - MEDIUM difficulty (only when AI involved)
        - f1: Red button - HARD difficulty (only when AI involved)
        - h1: Green button - Confirm and start game in selected mode

        Placed pieces show as white. Remaining board squares display mode text in white:
        - No pieces: Display "AA" (AI vs AI)
        - Only a1: Display "PA" (Player vs AI, player is white)
        - Only b1: Display "AP" (Player vs AI, player is black)
        - Both a1 and b1: Display "PP" (Player vs Player)

        Difficulty selection (only visible when AI is involved):
        - No difficulty selected: RANDOM
        - d1 selected: EASY
        - e1 selected: MEDIUM
        - f1 selected: HARD

        Args:
            placed_squares: List of squares where pieces have been placed
        """
        self.clear_all()

        # Define button squares and their colors
        a1 = Square(0, 0)
        b1 = Square(0, 1)
        d1 = Square(0, 3)
        e1 = Square(0, 4)
        f1 = Square(0, 5)
        h1 = Square(0, 7)

        # Letter patterns for mode text (rows 2-7, columns 1-6 for centered text)
        # Each letter is approximately 5 rows tall, 2-3 columns wide
        # 'A' pattern (col 1-2, rows 3-7)
        letter_a = [
            (3, 0),
            (4, 0),
            (5, 0),
            (6, 0),
            (7, 1),
            (5, 1),
            (5, 2),
            (3, 2),
            (4, 2),
            (6, 2),
        ]
        # 'P' pattern (col 1-2, rows 3-7)
        letter_p = [
            (3, 0),
            (4, 0),
            (5, 0),
            (6, 0),
            (7, 0),
            (7, 1),
            (5, 1),
            (6, 2),
        ]

        # Determine which mode is active based on placed pieces
        mode_text_squares = []

        a1_placed = a1 in placed_squares
        b1_placed = b1 in placed_squares
        d1_placed = d1 in placed_squares
        e1_placed = e1 in placed_squares
        f1_placed = f1 in placed_squares

        # Check if AI is involved (any mode except PvP)
        ai_involved = not (a1_placed and b1_placed)

        if not a1_placed and not b1_placed:
            # No pieces: Show AA (AI vs AI)
            mode_text_squares = letter_a + [(s[0], s[1] + 5) for s in letter_a]
        elif a1_placed and b1_placed:
            # Both pieces: Show PP (Player vs Player)
            mode_text_squares = letter_p + [(s[0], s[1] + 5) for s in letter_p]
        elif a1_placed:
            # Only a1: Show PA (Player vs AI, player white)
            mode_text_squares = letter_p + [(s[0], s[1] + 5) for s in letter_a]
        else:
            # Only b1: Show AP (Player vs AI, player black)
            mode_text_squares = letter_a + [(s[0], s[1] + 5) for s in letter_p]

        # Set button colors
        if a1 in placed_squares:
            self.set_square_color(a1, (200, 200, 200))  # White (selected)
        else:
            self.set_square_color(a1, (0, 150, 200))  # Light blue (white pieces)

        if b1 in placed_squares:
            self.set_square_color(b1, (200, 200, 200))  # White (selected)
        else:
            self.set_square_color(b1, (0, 0, 200))  # Blue (black pieces)

        if h1 in placed_squares:
            self.set_square_color(h1, (200, 200, 200))  # White (selected)
        else:
            self.set_square_color(h1, (0, 200, 0))  # Green (confirm button)

        # Show difficulty selection buttons only when AI is involved
        if ai_involved:
            # Only allow one difficulty to be selected at a time
            # If multiple are "placed", only the last one in priority (f1 > e1 > d1) is active
            if f1_placed:
                d1_active, e1_active, f1_active = False, False, True
            elif e1_placed:
                d1_active, e1_active, f1_active = False, True, False
            elif d1_placed:
                d1_active, e1_active, f1_active = True, False, False
            else:
                d1_active, e1_active, f1_active = False, False, False

            # d1: EASY difficulty (yellow)
            if d1_active:
                self.set_square_color(d1, (200, 200, 200))  # White (selected)
            else:
                self.set_square_color(d1, (200, 200, 0))  # Yellow

            # e1: MEDIUM difficulty (orange)
            if e1_active:
                self.set_square_color(e1, (200, 200, 200))  # White (selected)
            else:
                self.set_square_color(e1, (200, 100, 0))  # Orange

            # f1: HARD difficulty (red)
            if f1_active:
                self.set_square_color(f1, (200, 200, 200))  # White (selected)
            else:
                self.set_square_color(f1, (200, 0, 0))  # Red

        # Draw mode text in white
        for row, col in mode_text_squares:
            if 0 <= row < 8 and 0 <= col < 8:
                square = Square(row, col)
                # Don't override button squares
                if square not in [a1, b1, d1, e1, f1, h1]:
                    self.set_square_color(square, (200, 200, 200))  # White text

        self.show()

    def show_waiting_for_pieces(
        self, placed_squares: list[Square], correct_squares: list[Square]
    ) -> None:
        """
        Show board waiting for pieces to be placed in starting position.

        Squares where pieces should be placed are shown in RED.
        Squares where pieces have been correctly placed show in GREEN.
        All other squares are off.

        Args:
            placed_squares: Squares where pieces have been detected
            correct_squares: Squares where pieces should be in starting position
        """
        self.clear_all()

        # Show expected positions in RED
        for square in correct_squares:
            if square not in placed_squares:
                self.set_square_color(square, (200, 0, 0))  # RED - piece needed

        # Show placed pieces in GREEN
        for square in placed_squares:
            if square in correct_squares:
                self.set_square_color(square, (0, 200, 0))  # GREEN - correct placement

        self.show()

    def show_piece_placed_feedback(self, square: Square, is_correct: bool) -> None:
        """
        Show immediate feedback when a piece is placed.

        Args:
            square: Square where piece was placed
            is_correct: Whether piece was placed in correct position
        """
        if is_correct:
            # Bright green flash for correct placement
            self.set_square_color(square, (0, 200, 0))
        else:
            # Red flash for incorrect placement
            self.set_square_color(square, (200, 0, 0))
        self.show()

    def cleanup(self) -> None:
        """Clean up resources and turn off all LEDs."""
        self.clear_all()
        self.show()
