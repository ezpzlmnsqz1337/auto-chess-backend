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

from typing import Any

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

    def show_player_turn(self, is_white_turn: bool) -> None:
        """
        Briefly flash to indicate whose turn it is.

        Args:
            is_white_turn: True if white's turn, False if black's turn
        """
        color = LEDColors.WHITE_PLAYER if is_white_turn else LEDColors.BLACK_PLAYER
        # Flash the edges
        edge_squares = []
        for col in range(8):
            edge_squares.append(Square(0, col))  # Bottom rank
            edge_squares.append(Square(7, col))  # Top rank
        for row in range(1, 7):
            edge_squares.append(Square(row, 0))  # Left file
            edge_squares.append(Square(row, 7))  # Right file

        self.highlight_squares(edge_squares, color, clear_first=True)
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

    def cleanup(self) -> None:
        """Clean up resources and turn off all LEDs."""
        self.clear_all()
        self.show()
