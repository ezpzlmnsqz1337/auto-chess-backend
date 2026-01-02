"""Test reed switch controller functionality."""

import pytest

from src.reed_switch_controller import ReedSwitchController


def test_reed_switch_initialization() -> None:
    """Test reed switch controller can be initialized."""
    reed = ReedSwitchController()
    assert reed is not None
    reed.close()


def test_square_index_conversion() -> None:
    """Test conversion between square positions and indices."""
    reed = ReedSwitchController()

    # Test a1 (bottom-left)
    assert reed._square_to_index(0, 0) == 0
    assert reed._index_to_square(0) == (0, 0)

    # Test h8 (top-right)
    assert reed._square_to_index(7, 7) == 63
    assert reed._index_to_square(63) == (7, 7)

    # Test e4
    assert reed._square_to_index(3, 4) == 28
    assert reed._index_to_square(28) == (3, 4)

    reed.close()


def test_mux_channel_mapping() -> None:
    """Test multiplexer channel mapping."""
    reed = ReedSwitchController()

    # Mux 1: squares 0-15 (rows 1-2)
    mux, channel = reed._index_to_mux_channel(0)  # a1
    assert mux == 0 and channel == 0

    mux, channel = reed._index_to_mux_channel(7)  # h1
    assert mux == 0 and channel == 7

    mux, channel = reed._index_to_mux_channel(8)  # a2
    assert mux == 0 and channel == 8

    mux, channel = reed._index_to_mux_channel(15)  # h2
    assert mux == 0 and channel == 15

    # Mux 2: squares 16-31 (rows 3-4)
    mux, channel = reed._index_to_mux_channel(16)  # a3
    assert mux == 1 and channel == 0

    # Mux 3: squares 32-47 (rows 5-6)
    mux, channel = reed._index_to_mux_channel(32)  # a5
    assert mux == 2 and channel == 0

    # Mux 4: squares 48-63 (rows 7-8)
    mux, channel = reed._index_to_mux_channel(48)  # a7
    assert mux == 3 and channel == 0

    mux, channel = reed._index_to_mux_channel(63)  # h8
    assert mux == 3 and channel == 15

    reed.close()


def test_scan_all_squares() -> None:
    """Test scanning returns 64 values."""
    reed = ReedSwitchController()
    states = reed.scan_all_squares()

    assert len(states) == 64
    assert all(isinstance(state, bool) for state in states)

    reed.close()


def test_scan_with_debounce() -> None:
    """Test debounced scanning."""
    reed = ReedSwitchController()
    states = reed.scan_with_debounce()

    assert len(states) == 64
    assert all(isinstance(state, bool) for state in states)

    reed.close()


def test_get_occupied_squares() -> None:
    """Test getting occupied squares list."""
    reed = ReedSwitchController()
    reed.scan_with_debounce()
    occupied = reed.get_occupied_squares()

    assert isinstance(occupied, list)
    # All tuples should be (row, col) where both are 0-7
    for row, col in occupied:
        assert 0 <= row <= 7
        assert 0 <= col <= 7

    reed.close()


def test_board_state_display() -> None:
    """Test board state string representation."""
    reed = ReedSwitchController()
    reed.scan_with_debounce()
    display = reed.get_board_state_fen_like()

    assert isinstance(display, str)
    assert "a b c d e f g h" in display  # Should have file labels
    lines = display.split("\n")
    assert len(lines) == 9  # 8 ranks + 1 file label line

    reed.close()


def test_read_single_square() -> None:
    """Test reading a single square."""
    reed = ReedSwitchController()

    # Read e4 (row=3, col=4)
    state = reed.read_square(3, 4)
    assert isinstance(state, bool)

    # Read all corners
    assert isinstance(reed.read_square(0, 0), bool)  # a1
    assert isinstance(reed.read_square(0, 7), bool)  # h1
    assert isinstance(reed.read_square(7, 0), bool)  # a8
    assert isinstance(reed.read_square(7, 7), bool)  # h8

    reed.close()


def test_detect_changes() -> None:
    """Test change detection between scans."""
    reed = ReedSwitchController()

    # First scan to establish baseline
    reed.scan_with_debounce()

    # Second scan to detect changes
    added, removed = reed.detect_changes()

    assert isinstance(added, list)
    assert isinstance(removed, list)

    reed.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
