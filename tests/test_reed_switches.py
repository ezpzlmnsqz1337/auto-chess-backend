"""Test reed switch controller functionality."""

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pytest

from reed_switch_controller import ReedSwitchController
from tests.visualization import draw_reed_switch_state, setup_reed_switch_plot

# Create output directory for visualizations
OUTPUT_DIR = Path(__file__).parent / "output" / "reed_switches"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from chess_game import ChessGame


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


def test_piece_returned_to_same_square() -> None:
    """Test that picking up and replacing a piece on the same square is handled."""
    from unittest.mock import patch

    reed = ReedSwitchController()

    # Setup initial state with a piece on e4
    initial = [False] * 64
    e4_idx = reed._square_to_index(3, 4)
    initial[e4_idx] = True

    # Prepare all states upfront
    without_piece = [False] * 64  # All empty, piece picked up
    with_piece_back = initial.copy()  # Piece back on e4

    # Mock scan_with_debounce to return our controlled states in sequence
    states = [
        initial.copy(),  # Initial scan - establishes baseline
        without_piece.copy(),  # Piece removed
        with_piece_back.copy(),  # Piece returned
    ]
    call_count = [0]

    def mock_scan() -> list[bool]:
        result = states[call_count[0]].copy()
        call_count[0] += 1
        return result

    with patch.object(reed, "scan_with_debounce", side_effect=mock_scan):
        # First scan establishes baseline (compares with empty initial state)
        added, removed = reed.detect_changes()
        # Will see e4 as "added" since board started empty
        assert len(added) == 1  # e4 added compared to empty board
        assert added[0] == (3, 4)

        # Second scan: piece removed from e4
        added, removed = reed.detect_changes()
        assert len(removed) == 1
        assert removed[0] == (3, 4)
        assert len(added) == 0

        # Third scan: piece returned to same square e4
        added, removed = reed.detect_changes()
        assert len(added) == 1
        assert added[0] == (3, 4)
        assert len(removed) == 0

    reed.close()


def test_wait_for_move_ignores_same_square() -> None:
    """Test that wait_for_move ignores piece returned to same square."""
    from unittest.mock import patch

    reed = ReedSwitchController()

    # Mock detect_changes to simulate:
    # 1. Piece removed from e4
    # 2. Piece added back to e4 (should be ignored)
    # 3. Piece removed from d4
    # 4. Piece added to e5 (valid move)
    mock_changes = [
        ([], [(3, 4)]),  # Removed from e4
        ([(3, 4)], []),  # Added back to e4 - should reset
        ([], [(3, 3)]),  # Removed from d4
        ([(4, 4)], []),  # Added to e5 - valid move
    ]

    call_count = [0]

    def side_effect() -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        if call_count[0] < len(mock_changes):
            result = mock_changes[call_count[0]]
            call_count[0] += 1
            return result
        return ([], [])

    with (
        patch.object(reed, "detect_changes", side_effect=side_effect),
        patch("time.time", side_effect=[0, 0.1, 0.2, 0.3, 0.4] + [100] * 100),
        patch("time.sleep"),
        patch("builtins.print"),
    ):
        result = reed.wait_for_move(timeout=30.0)

    # Should return d4 -> e5, not e4 -> e4
    assert result is not None
    assert result[0] == (3, 3)  # From d4
    assert result[1] == (4, 4)  # To e5

    reed.close()


def test_visualize_starting_position() -> None:
    """Test and visualize standard chess starting position."""
    reed = ReedSwitchController()

    # Simulate standard chess starting position
    # Bottom two ranks (white) and top two ranks (black)
    starting_position = [False] * 64
    for square_idx in range(16):  # Ranks 1-2 (white pieces)
        starting_position[square_idx] = True
    for square_idx in range(48, 64):  # Ranks 7-8 (black pieces)
        starting_position[square_idx] = True

    # Manually set the board state for visualization
    reed._board_state = starting_position

    # Plot the board
    fig, ax = plt.subplots(figsize=(10, 10))
    _draw_reed_switch_board(ax, reed, "Chess Starting Position")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "reed_starting_position.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("✓ Starting position visualization saved")
    reed.close()


def test_visualize_move_sequence() -> None:
    """Test and visualize a sequence of moves (e2-e4, e7-e5)."""
    from chess_game import ChessGame, Square

    reed = ReedSwitchController()

    # Create actual chess games for each position
    game_start = ChessGame()
    game_after_e4 = ChessGame()
    game_after_e4.make_move(Square.from_notation("e2"), Square.from_notation("e4"))
    game_after_e5 = ChessGame()
    game_after_e5.make_move(Square.from_notation("e2"), Square.from_notation("e4"))
    game_after_e5.make_move(Square.from_notation("e7"), Square.from_notation("e5"))

    # Track indices for highlighting
    e2_idx = reed._square_to_index(1, 4)
    e4_idx = reed._square_to_index(3, 4)
    e7_idx = reed._square_to_index(6, 4)
    e5_idx = reed._square_to_index(4, 4)

    # Create figure with subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Plot each position using actual chess games
    _draw_reed_switch_board_with_game(axes[0], game_start, "Starting Position")
    _draw_reed_switch_board_with_game(axes[1], game_after_e4, "After 1. e4")
    _highlight_move(axes[1], reed, e2_idx, e4_idx)
    _draw_reed_switch_board_with_game(axes[2], game_after_e5, "After 1. ... e5")
    _highlight_move(axes[2], reed, e7_idx, e5_idx)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "reed_move_sequence.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("✓ Move sequence visualization saved")
    reed.close()


def test_visualize_change_detection() -> None:
    """Test and visualize change detection between board states."""
    reed = ReedSwitchController()

    # Initial position (e4, d4, e5, d5 occupied - center control)
    initial = [False] * 64
    e4_idx = reed._square_to_index(3, 4)
    d4_idx = reed._square_to_index(3, 3)
    e5_idx = reed._square_to_index(4, 4)
    d5_idx = reed._square_to_index(4, 3)
    initial[e4_idx] = True
    initial[d4_idx] = True
    initial[e5_idx] = True
    initial[d5_idx] = True

    # After change: Knight moves (simulate Nf3 - add f3, capture on d5)
    after_change = initial.copy()
    f3_idx = reed._square_to_index(2, 5)  # Row 2 (rank 3), column 5 (f file)
    after_change[f3_idx] = True  # Knight to f3
    after_change[d5_idx] = False  # Piece captured on d5

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Plot initial position
    reed._board_state = initial
    _draw_reed_switch_board(axes[0], reed, "Initial Position")

    # Plot final position
    reed._board_state = after_change
    _draw_reed_switch_board(axes[1], reed, "After Changes")

    # Plot changes visualization
    axes[2].set_xlim(-0.5, 8)
    axes[2].set_ylim(-0.5, 8)
    axes[2].set_aspect("equal")
    axes[2].set_title("Changes Detected", fontsize=14, fontweight="bold")
    axes[2].set_xlabel("File (a-h)", fontsize=12, fontweight="bold")
    axes[2].set_ylabel("Rank (1-8)", fontsize=12, fontweight="bold")

    # Draw board grid
    _draw_board_grid(axes[2])

    # Highlight changes
    # Removed (d5)
    row, col = reed._index_to_square(d5_idx)
    _highlight_square(axes[2], row, col, color="red", alpha=0.5, label="Removed")

    # Added (f3)
    row, col = reed._index_to_square(f3_idx)
    _highlight_square(axes[2], row, col, color="green", alpha=0.5, label="Added")

    # Add remaining pieces (no change)
    for idx in [e4_idx, d4_idx, e5_idx]:
        if initial[idx] and after_change[idx]:
            row, col = reed._index_to_square(idx)
            _draw_piece(axes[2], row, col, color="blue")

    _add_board_labels(axes[2])
    axes[2].legend(loc="upper right", fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "reed_change_detection.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("✓ Change detection visualization saved")
    reed.close()


def _draw_reed_switch_board(ax: "Axes", reed: ReedSwitchController, title: str) -> None:
    """Draw chess board with reed switch states using actual chess pieces."""
    from chess_game import ChessGame

    setup_reed_switch_plot(ax, title=title)

    # Create a chess game from the reed switch board state
    # Assume starting position if we have pieces on ranks 1-2 and 7-8
    game = ChessGame()
    has_starting_position = all(reed._board_state[i] for i in range(16)) and all(
        reed._board_state[i] for i in range(48, 64)
    )

    if has_starting_position:
        # Use actual starting position
        draw_reed_switch_state(ax, game=game)
    else:
        # Show simple indicators if not a standard position
        draw_reed_switch_state(ax, board_state=reed._board_state)


def _draw_reed_switch_board_with_game(ax: "Axes", game: "ChessGame", title: str) -> None:
    """Draw chess board with reed switch states from a ChessGame object."""
    setup_reed_switch_plot(ax, title=title)
    draw_reed_switch_state(ax, game=game)


def _draw_board_grid(ax: "Axes") -> None:
    """Draw chess board grid with alternating squares using unified function."""
    from tests.test_utils import draw_chess_board_grid

    draw_chess_board_grid(ax, show_capture_areas=True, use_motor_coordinates=False)


def _draw_piece(ax: "Axes", row: int, col: int, color: str = "black") -> None:
    """Draw a piece (circle) at the given board position (centered on square)."""
    circle = mpatches.Circle(
        (col + 0.5, row + 0.5), 0.3, facecolor=color, edgecolor="darkgray", linewidth=2
    )
    ax.add_patch(circle)


def _highlight_square(
    ax: "Axes", row: int, col: int, color: str = "yellow", alpha: float = 0.6, label: str = ""
) -> None:
    """Highlight a square on the board."""
    rect = mpatches.Rectangle(
        (col, row), 1, 1, facecolor=color, alpha=alpha, edgecolor=color, linewidth=3
    )
    ax.add_patch(rect)
    if label:
        ax.plot([], [], "s", color=color, markersize=10, label=label)


def _highlight_move(ax: "Axes", reed: ReedSwitchController, from_idx: int, to_idx: int) -> None:
    """Highlight a move with an arrow."""
    from_row, from_col = reed._index_to_square(from_idx)
    to_row, to_col = reed._index_to_square(to_idx)
    ax.annotate(
        "",
        xy=(to_col + 0.5, to_row + 0.5),
        xytext=(from_col + 0.5, from_row + 0.5),
        arrowprops={
            "arrowstyle": "->",
            "color": "red",
            "lw": 3,
            "alpha": 0.7,
        },
    )


def _add_board_labels(ax: "Axes") -> None:
    """Add file and rank labels to the board with capture areas visible."""
    # Position labels at square centers
    ax.set_xticks([i + 0.5 for i in range(8)])
    ax.set_xticklabels([chr(ord("a") + i) for i in range(8)])
    ax.set_yticks([i + 0.5 for i in range(8)])
    ax.set_yticklabels([str(i + 1) for i in range(8)])

    # Set limits to show capture areas
    ax.set_xlim(-2.5, 10.5)
    ax.set_ylim(-0.5, 8.5)
    ax.set_aspect("equal")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
