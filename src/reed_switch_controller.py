"""Reed switch controller for chess piece detection.

Uses 4× CD74HC4067 16-channel multiplexers to read 64 reed switches,
one under each square of the chess board.
"""

import time

try:
    from gpiozero import DigitalInputDevice, DigitalOutputDevice
except ImportError:
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory

    Device.pin_factory = MockFactory()
    from gpiozero import DigitalInputDevice, DigitalOutputDevice

from src import config


class ReedSwitchController:
    """Controls reed switch multiplexers for piece detection."""

    def __init__(self) -> None:
        """Initialize multiplexer control pins and signal readers."""
        # Address pins (shared across all multiplexers)
        self.s0 = DigitalOutputDevice(config.MUX_S0_PIN)
        self.s1 = DigitalOutputDevice(config.MUX_S1_PIN)
        self.s2 = DigitalOutputDevice(config.MUX_S2_PIN)
        self.s3 = DigitalOutputDevice(config.MUX_S3_PIN)

        # Signal pins (one per multiplexer)
        # Using pull_up=False enables internal pull-down resistor
        # Reed switch closes to 3.3V, so pin reads HIGH when switch is closed
        self.sig_pins = [DigitalInputDevice(pin, pull_up=False) for pin in config.MUX_SIG_PINS]

        # Current board state (64 squares, True = piece present)
        self._board_state: list[bool] = [False] * 64

        # Previous board state for change detection
        self._previous_state: list[bool] = [False] * 64

        # Debounce tracking
        self._state_change_times: list[float] = [0.0] * 64
        self._debounced_state: list[bool] = [False] * 64

        print("🔌 Reed switch controller initialized")

    def _set_mux_address(self, channel: int) -> None:
        """Set multiplexer address to select a channel (0-15).

        Args:
            channel: Channel number 0-15
        """
        self.s0.value = (channel & 0x01) != 0
        self.s1.value = (channel & 0x02) != 0
        self.s2.value = (channel & 0x04) != 0
        self.s3.value = (channel & 0x08) != 0

    def _square_to_index(self, row: int, col: int) -> int:
        """Convert board position to linear index (0-63).

        Args:
            row: Row number 0-7 (rank 1-8)
            col: Column number 0-7 (file a-h)

        Returns:
            Linear index 0-63
        """
        return row * 8 + col

    def _index_to_square(self, index: int) -> tuple[int, int]:
        """Convert linear index to board position.

        Args:
            index: Linear index 0-63

        Returns:
            Tuple of (row, col) where row=0-7, col=0-7
        """
        return index // 8, index % 8

    def _index_to_mux_channel(self, index: int) -> tuple[int, int]:
        """Convert square index to multiplexer and channel.

        Args:
            index: Square index 0-63

        Returns:
            Tuple of (mux_index, channel) where mux_index=0-3, channel=0-15
        """
        mux_index = index // 16  # Which multiplexer (0-3)
        channel = index % 16  # Which channel on that mux (0-15)
        return mux_index, channel

    def read_square(self, row: int, col: int) -> bool:
        """Read a single square's reed switch state.

        Args:
            row: Row number 0-7
            col: Column number 0-7

        Returns:
            True if piece detected, False otherwise
        """
        index = self._square_to_index(row, col)
        mux_index, channel = self._index_to_mux_channel(index)

        # Set multiplexer address
        self._set_mux_address(channel)

        # Small delay for multiplexer to settle (datasheet: ~1-5μs)
        time.sleep(0.00001)  # 10 microseconds

        # Read signal pin for this multiplexer
        return bool(self.sig_pins[mux_index].is_active)

    def scan_all_squares(self) -> list[bool]:
        """Scan all 64 squares and return their states.

        Returns:
            List of 64 booleans (True = piece present)
        """
        states = []

        for index in range(64):
            mux_index, channel = self._index_to_mux_channel(index)
            self._set_mux_address(channel)
            time.sleep(0.00001)  # 10μs settling time
            states.append(self.sig_pins[mux_index].is_active)

        self._board_state = states
        return states

    def scan_with_debounce(self) -> list[bool]:
        """Scan all squares with debouncing to filter noise.

        Returns:
            List of 64 debounced booleans (True = piece present)
        """
        current_time = time.time()
        raw_states = self.scan_all_squares()

        for i in range(64):
            # If state changed, record the time
            if raw_states[i] != self._previous_state[i]:
                self._state_change_times[i] = current_time
                self._previous_state[i] = raw_states[i]

            # If state has been stable for debounce time, accept it
            time_since_change = current_time - self._state_change_times[i]
            if time_since_change >= config.REED_SWITCH_DEBOUNCE_TIME:
                self._debounced_state[i] = raw_states[i]

        return self._debounced_state.copy()

    def get_occupied_squares(self) -> list[tuple[int, int]]:
        """Get list of all squares with pieces on them.

        Returns:
            List of (row, col) tuples for occupied squares
        """
        occupied = []
        for i in range(64):
            if self._debounced_state[i]:
                row, col = self._index_to_square(i)
                occupied.append((row, col))
        return occupied

    def detect_changes(self) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        """Detect which squares changed since last scan.

        Returns:
            Tuple of (added_pieces, removed_pieces) as lists of (row, col) tuples
        """
        current = self.scan_with_debounce()
        added = []
        removed = []

        for i in range(64):
            if current[i] and not self._board_state[i]:
                # Piece added
                row, col = self._index_to_square(i)
                added.append((row, col))
            elif not current[i] and self._board_state[i]:
                # Piece removed
                row, col = self._index_to_square(i)
                removed.append((row, col))

        self._board_state = current
        return added, removed

    def wait_for_move(
        self, timeout: float = config.MOVE_DETECTION_TIMEOUT
    ) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Wait for a human player to make a move.

        Detects a piece being picked up (removed) and then placed (added).

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Tuple of ((from_row, from_col), (to_row, to_col)) or None if timeout
        """
        start_time = time.time()
        from_square: tuple[int, int] | None = None
        scan_interval = 1.0 / config.REED_SWITCH_SCAN_RATE

        print("🎯 Waiting for move... (pick up a piece)")

        while (time.time() - start_time) < timeout:
            added, removed = self.detect_changes()

            if removed and from_square is None:
                # Piece picked up
                from_square = removed[0]
                row, col = from_square
                print(f"✋ Piece picked up from {chr(97 + col)}{row + 1}")

            elif added and from_square is not None:
                # Piece placed
                to_square = added[0]
                row, col = to_square
                print(f"✅ Piece placed at {chr(97 + col)}{row + 1}")
                return from_square, to_square

            time.sleep(scan_interval)

        print("⏱️ Move detection timeout")
        return None

    def get_board_state_fen_like(self) -> str:
        """Get a visual representation of the board state.

        Returns:
            String showing board with 1 for occupied, 0 for empty
        """
        lines = []
        for row in range(7, -1, -1):  # Start from rank 8 down to rank 1
            line = f"{row + 1} "
            for col in range(8):
                index = self._square_to_index(row, col)
                line += "1 " if self._debounced_state[index] else "0 "
            lines.append(line)
        lines.append("  a b c d e f g h")
        return "\n".join(lines)

    def close(self) -> None:
        """Release GPIO resources."""
        self.s0.close()
        self.s1.close()
        self.s2.close()
        self.s3.close()
        for pin in self.sig_pins:
            pin.close()
        print("🔌 Reed switch controller closed")
