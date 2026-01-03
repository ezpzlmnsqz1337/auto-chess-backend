"""
Comprehensive integration test for auto-chess system.

This test demonstrates the complete workflow:
- Chess board state with pieces
- Magnet movement visualization using REAL motor controller
- Motor speed analysis with actual acceleration profiles
- LED feedback visualization
"""

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import chess
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import config
from chess_game import ChessGame, PieceType, Player, Square
from led import WS2812BController
from src.ai import ChessAI, DifficultyLevel
from src.board_navigation import square_to_steps
from tests.test_utils import (
    capture_movement_path,
    create_test_controller,
    draw_chess_board_grid,
    plot_path_with_magnet_state,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

# Create output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "integration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class GameState(TypedDict):
    """Type definition for game state dictionary."""

    game: ChessGame
    title: str
    subtitle: str
    magnet_square: Square | None
    is_homed: bool
    path_x: list[float]
    path_y: list[float]
    magnet_states: list[bool]
    speeds: list[float]
    time: list[float]
    led_state: WS2812BController


def _draw_chess_pieces(ax: "Axes", game: ChessGame) -> None:
    """
    Draw chess pieces on the board.
    Reusable function extracted from test_chess_game.py.

    Args:
        ax: Matplotlib axes
        game: Chess game instance
    """
    piece_symbols = {
        PieceType.PAWN: "♟",
        PieceType.KNIGHT: "♞",
        PieceType.BISHOP: "♝",
        PieceType.ROOK: "♜",
        PieceType.QUEEN: "♛",
        PieceType.KING: "♚",
    }

    for square, piece in game.board.items():
        symbol = piece_symbols[piece.piece_type]
        # White pieces with black outline, black pieces solid
        if piece.player == Player.WHITE:
            text = ax.text(
                square.col + 0.5,
                square.row + 0.5,
                symbol,
                fontsize=36,
                ha="center",
                va="center",
                color="white",
                weight="bold",
                zorder=10,
            )
            # Add black outline to white pieces for visibility
            text.set_path_effects(
                [
                    path_effects.Stroke(linewidth=3, foreground="black"),
                    path_effects.Normal(),
                ]
            )
        else:
            ax.text(
                square.col + 0.5,
                square.row + 0.5,
                symbol,
                fontsize=36,
                ha="center",
                va="center",
                color="black",
                weight="bold",
                zorder=10,
            )


def _draw_magnet_position(
    ax: "Axes",
    path_x: list[float],
    path_y: list[float],
    is_homed: bool = False,
) -> None:
    """
    Draw magnet position on the board.

    Args:
        ax: Matplotlib axes in motor coordinates
        path_x: X coordinates of path (empty if homed)
        path_y: Y coordinates of path (empty if homed)
        is_homed: If True, show homed position
    """
    if is_homed or not path_x or not path_y:
        # Homed position is at (0,0) in board coordinates (bottom-left corner)
        magnet_x: float = 0.0
        magnet_y: float = 0.0
        color = "gray"
        label = "Homed"
    else:
        # Magnet is at the last position in the path
        magnet_x = path_x[-1]
        magnet_y = path_y[-1]
        color = "red"
        label = "Magnet"

    # Draw magnet as circle with cross
    ax.plot(magnet_x, magnet_y, "o", color=color, markersize=12, label=label, zorder=15)
    ax.plot(magnet_x, magnet_y, "x", color="white", markersize=8, markeredgewidth=2, zorder=16)


def _smooth_velocities(velocities: list[float], window_size: int = 5) -> list[float]:
    """
    Smooth velocity data using a moving average to reduce Bresenham oscillations.

    Args:
        velocities: Raw velocity samples
        window_size: Number of samples to average (must be odd)

    Returns:
        Smoothed velocity data
    """
    if len(velocities) < window_size:
        return velocities

    smoothed = []
    half_window = window_size // 2

    for i in range(len(velocities)):
        # Calculate window bounds
        start = max(0, i - half_window)
        end = min(len(velocities), i + half_window + 1)
        # Average velocities in window
        window_avg = sum(velocities[start:end]) / (end - start)
        smoothed.append(window_avg)

    return smoothed


def test_complete_game_integration() -> None:
    """
    Complete integration test showing 4 game states:
    - Column 1: Starting position (homed)
    - Column 2: After white's first move
    - Column 3: After black's first move
    - Column 4: Knight move jumping over pieces

    Each column shows:
    - Row 1: Chess board with pieces
    - Row 2: Magnet movement path (cumulative) using REAL motor controller
    - Row 3: Magnet speed profile (actual acceleration/deceleration)
    - Row 4: LED state after move
    """
    # Initialize game and motor controller
    game = ChessGame()
    board = chess.Board()
    ai = ChessAI(DifficultyLevel.MEDIUM)
    controller = create_test_controller()
    assert controller.electromagnet is not None, "Electromagnet required for testing"

    # Track game states
    states: list[GameState] = []

    try:
        # State 1: Starting position (homed)
        led_start = WS2812BController(use_mock=True)
        led_start.show_player_turn(game)  # Show white pieces

        states.append(
            {
                "game": ChessGame(),  # Copy of initial state
                "title": "Starting Position",
                "subtitle": "Magnet Homed, White to Move",
                "magnet_square": None,
                "is_homed": True,
                "path_x": [],
                "path_y": [],
                "magnet_states": [],
                "speeds": [],
                "time": [],
                "led_state": led_start,
            }
        )

        # TODO: Track current magnet position for proper move continuity
        # current_pos = (0, 0)  # Start at home

        # State 2: White's first move
        move_white = ai.get_move(board)
        from_sq_white = Square(move_white.from_square // 8, move_white.from_square % 8)
        to_sq_white = Square(move_white.to_square // 8, move_white.to_square % 8)

        # Calculate positions
        from_x, from_y = square_to_steps(from_sq_white.row, from_sq_white.col)
        to_x, to_y = square_to_steps(to_sq_white.row, to_sq_white.col)

        # Magnet OFF: Move from home to piece location
        controller.electromagnet.off()
        target_positions = [(from_x, from_y)]
        positions, timestamps, speeds, magnet_states = capture_movement_path(
            controller, target_positions, sample_rate=20
        )

        # Magnet ON: Pick up piece and move to destination
        controller.electromagnet.on()
        target_positions = [(to_x, to_y)]
        pos2, time2, speed2, mag2 = capture_movement_path(
            controller, target_positions, sample_rate=20
        )

        # Combine the segments (offset time by last timestamp)
        positions.extend(pos2[1:])  # Skip duplicate starting position
        timestamps.extend([t + timestamps[-1] for t in time2[1:]])
        speeds.extend(speed2[1:])
        magnet_states.extend(mag2[1:])

        # Magnet OFF: Release piece
        controller.electromagnet.off()
        # Make move and update LED
        game.make_move(from_sq_white, to_sq_white)
        board.push(move_white)

        led_white = WS2812BController(use_mock=True)
        led_white.show_player_turn(game)

        # Create game state copy
        game_copy_white = ChessGame()
        game_copy_white.board.clear()
        for sq, piece in game.board.items():
            game_copy_white.board[sq] = piece
        game_copy_white.current_player = game.current_player

        # Convert positions to mm for plotting
        path_x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
        path_y_mm = [y / config.STEPS_PER_MM for _, y in positions]

        states.append(
            {
                "game": game_copy_white,
                "title": "Move 1: White",
                "subtitle": f"{from_sq_white.to_notation()} → {to_sq_white.to_notation()}",
                "magnet_square": to_sq_white,
                "is_homed": False,
                "path_x": list(path_x_mm),
                "path_y": list(path_y_mm),
                "magnet_states": list(magnet_states),
                "speeds": list(speeds),
                "time": list(timestamps),
                "led_state": led_white,
            }
        )

        # State 3: Black's first move
        move_black = ai.get_move(board)
        from_sq_black = Square(move_black.from_square // 8, move_black.from_square % 8)
        to_sq_black = Square(move_black.to_square // 8, move_black.to_square % 8)

        # Calculate positions
        from_x, from_y = square_to_steps(from_sq_black.row, from_sq_black.col)
        to_x, to_y = square_to_steps(to_sq_black.row, to_sq_black.col)

        # Magnet OFF: Move from previous position to piece location
        controller.electromagnet.off()
        target_positions = [(from_x, from_y)]
        positions, timestamps, speeds, magnet_states = capture_movement_path(
            controller, target_positions, sample_rate=20
        )

        # Magnet ON: Pick up piece and move to destination
        controller.electromagnet.on()
        target_positions = [(to_x, to_y)]
        pos2, time2, speed2, mag2 = capture_movement_path(
            controller, target_positions, sample_rate=20
        )

        # Combine the segments (offset time by last timestamp)
        positions.extend(pos2[1:])  # Skip duplicate starting position
        timestamps.extend([t + timestamps[-1] for t in time2[1:]])
        speeds.extend(speed2[1:])
        magnet_states.extend(mag2[1:])

        # Magnet OFF: Release piece
        controller.electromagnet.off()

        # Make move and update LED
        game.make_move(from_sq_black, to_sq_black)
        board.push(move_black)

        led_black = WS2812BController(use_mock=True)
        led_black.show_player_turn(game)

        # Create game state copy
        game_copy_black = ChessGame()
        game_copy_black.board.clear()
        for sq, piece in game.board.items():
            game_copy_black.board[sq] = piece
        game_copy_black.current_player = game.current_player

        # Convert to mm (non-cumulative)
        path_x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
        path_y_mm = [y / config.STEPS_PER_MM for _, y in positions]

        states.append(
            {
                "game": game_copy_black,
                "title": "Move 2: Black",
                "subtitle": f"{from_sq_black.to_notation()} → {to_sq_black.to_notation()}",
                "magnet_square": to_sq_black,
                "is_homed": False,
                "path_x": list(path_x_mm),
                "path_y": list(path_y_mm),
                "magnet_states": list(magnet_states),
                "speeds": list(speeds),
                "time": list(timestamps),
                "led_state": led_black,
            }
        )

        # State 4: Manual knight move (b1 to c3) - knight can jump over pieces
        from_sq_knight = Square.from_notation("b1")
        to_sq_knight = Square.from_notation("c3")

        # Calculate positions
        from_x, from_y = square_to_steps(from_sq_knight.row, from_sq_knight.col)
        to_x, to_y = square_to_steps(to_sq_knight.row, to_sq_knight.col)

        # Magnet OFF: Move from previous position to piece location
        controller.electromagnet.off()
        target_positions = [(from_x, from_y)]
        positions, timestamps, speeds, magnet_states = capture_movement_path(
            controller, target_positions, sample_rate=20
        )

        # Magnet ON: Pick up piece and move to destination
        controller.electromagnet.on()
        target_positions = [(to_x, to_y)]
        pos2, time2, speed2, mag2 = capture_movement_path(
            controller, target_positions, sample_rate=20
        )

        # Combine the segments (offset time by last timestamp)
        positions.extend(pos2[1:])  # Skip duplicate starting position
        timestamps.extend([t + timestamps[-1] for t in time2[1:]])
        speeds.extend(speed2[1:])
        magnet_states.extend(mag2[1:])

        # Magnet OFF: Release piece
        controller.electromagnet.off()

        # Make move on both boards
        game.make_move(from_sq_knight, to_sq_knight)
        # Create python-chess move and push it
        knight_move = chess.Move.from_uci("b1c3")
        board.push(knight_move)

        led_knight = WS2812BController(use_mock=True)
        led_knight.show_player_turn(game)  # Will show black pieces (black's turn)

        # Create game state copy
        game_copy_knight = ChessGame()
        game_copy_knight.board.clear()
        for sq, piece in game.board.items():
            game_copy_knight.board[sq] = piece
        game_copy_knight.current_player = game.current_player

        # Convert to mm (non-cumulative)
        path_x_mm = [x / config.STEPS_PER_MM for x, _ in positions]
        path_y_mm = [y / config.STEPS_PER_MM for _, y in positions]

        states.append(
            {
                "game": game_copy_knight,
                "title": "Move 3: White Knight",
                "subtitle": f"{from_sq_knight.to_notation()} → {to_sq_knight.to_notation()}",
                "magnet_square": to_sq_knight,
                "is_homed": False,
                "path_x": list(path_x_mm),
                "path_y": list(path_y_mm),
                "magnet_states": list(magnet_states),
                "speeds": list(speeds),
                "time": list(timestamps),
                "led_state": led_knight,
            }
        )

        # Create 4x4 plot
        fig = plt.figure(figsize=(24, 24))
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.25)

        for col_idx, state in enumerate(states):
            # Row 1: Chess board with pieces
            ax1 = fig.add_subplot(gs[0, col_idx])
            draw_chess_board_grid(ax1, show_capture_areas=False, use_motor_coordinates=False)
            _draw_chess_pieces(ax1, state["game"])
            ax1.set_title(f"{state['title']}\n{state['subtitle']}", fontsize=11, fontweight="bold")
            ax1.set_aspect("equal")

            # Row 2: Magnet movement path (motor coordinates)
            ax2 = fig.add_subplot(gs[1, col_idx])
            draw_chess_board_grid(ax2, show_capture_areas=True, use_motor_coordinates=True)

            if state["path_x"] and state["path_y"]:
                plot_path_with_magnet_state(
                    ax2, state["path_x"], state["path_y"], state["magnet_states"]
                )

            _draw_magnet_position(ax2, state["path_x"], state["path_y"], state["is_homed"])

            ax2.set_title("Magnet Movement (This Move)", fontsize=10)
            ax2.set_xlabel("X Position (mm)")
            ax2.set_ylabel("Y Position (mm)")
            ax2.set_aspect("equal")

            # Row 3: Speed profile
            ax3 = fig.add_subplot(gs[2, col_idx])
            if state["time"] and state["speeds"]:
                ax3.plot(state["time"], state["speeds"], linewidth=2, color="#2E86AB", alpha=0.9)
                avg_speed = sum(state["speeds"]) / len(state["speeds"])
                max_speed = max(state["speeds"])
                ax3.axhline(
                    y=avg_speed,
                    color="orange",
                    linestyle="--",
                    linewidth=1.5,
                    label=f"Avg: {avg_speed:.0f} mm/s",
                )
                ax3.text(
                    0.98,
                    0.95,
                    f"Max: {max_speed:.0f} mm/s",
                    transform=ax3.transAxes,
                    fontsize=9,
                    va="top",
                    ha="right",
                    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
                )
            ax3.set_title("Magnet Speed Profile", fontsize=10)
            ax3.set_xlabel("Time (s)")
            ax3.set_ylabel("Speed (mm/s)")
            ax3.grid(True, alpha=0.3)
            if state["speeds"]:
                ax3.legend(loc="upper left", fontsize=8)

            # Row 4: LED state
            ax4 = fig.add_subplot(gs[3, col_idx])
            draw_chess_board_grid(ax4, show_capture_areas=True, use_motor_coordinates=False)

            # Draw LED colors from mock controller
            led_controller = state["led_state"]

            # Helper function to draw LED square
            def draw_led_overlay(
                x_pos: float,
                y_pos: float,
                led_index: int,
                color: tuple[int, int, int],
                chess_label: str | None = None,
            ) -> None:
                """Draw LED square with color, LED index, and optional chess notation."""
                # Normalize RGB to 0-1 range
                color_normalized = (color[0] / 255, color[1] / 255, color[2] / 255)
                # Add colored square overlay (slightly transparent to show grid)
                ax4.add_patch(
                    Rectangle(
                        (x_pos, y_pos),
                        1,
                        1,
                        linewidth=0,
                        facecolor=color_normalized,
                        alpha=0.8,
                        zorder=5,
                    )
                )

                text_color = "white" if sum(color) < 384 else "black"

                if chess_label:
                    # Show both chess notation and LED index
                    ax4.text(
                        x_pos + 0.5,
                        y_pos + 0.65,
                        chess_label,
                        ha="center",
                        va="center",
                        fontsize=7,
                        color=text_color,
                        weight="bold",
                        zorder=6,
                    )
                    ax4.text(
                        x_pos + 0.5,
                        y_pos + 0.35,
                        str(led_index),
                        ha="center",
                        va="center",
                        fontsize=5,
                        color=text_color,
                        alpha=0.7,
                        zorder=6,
                    )
                else:
                    # Just show LED index for capture areas
                    ax4.text(
                        x_pos + 0.5,
                        y_pos + 0.5,
                        str(led_index),
                        ha="center",
                        va="center",
                        fontsize=6,
                        color=text_color,
                        weight="bold",
                        zorder=6,
                    )

            # Calculate gap for positioning
            gap_in_squares = config.CAPTURE_OFFSET_MM / config.SQUARE_SIZE_MM

            # Draw left capture area LEDs 0-15 (columns -2, -1)
            led_index = 0
            for row in range(config.BOARD_ROWS):
                for col in range(-config.CAPTURE_COLS, 0):
                    x_pos = col - gap_in_squares
                    color = (0, 0, 0)  # Black/off - no data yet
                    draw_led_overlay(x_pos, row, led_index, color)
                    led_index += 1

            # Draw main board LEDs 16-79 (columns 0-7)
            led_index = 16
            for row in range(config.BOARD_ROWS):
                for col in range(config.BOARD_COLS):
                    square_led = Square(row, col)
                    color = led_controller.get_square_color(square_led)
                    chess_label = square_led.to_notation()  # a1, b1, etc.
                    draw_led_overlay(col, row, led_index, color, chess_label)
                    led_index += 1

            # Draw right capture area LEDs 80-95 (columns 8, 9)
            led_index = 80
            for row in range(config.BOARD_ROWS):
                for col in range(config.BOARD_COLS, config.BOARD_COLS + config.CAPTURE_COLS):
                    x_pos = col + gap_in_squares
                    color = (0, 0, 0)  # Black/off - no data yet
                    draw_led_overlay(x_pos, row, led_index, color)
                    led_index += 1

            ax4.set_title("LED Feedback", fontsize=10)
            ax4.set_aspect("equal")

        fig.suptitle(
            "Complete Auto-Chess Integration Test\nUsing Real Motor Controller with Acceleration",
            fontsize=16,
            fontweight="bold",
            y=0.995,
        )

        # Save plot
        output_path = OUTPUT_DIR / "complete_integration.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Saved complete integration visualization: {output_path}")

    except Exception as e:
        print(f"Error during integration test: {e}")
        raise
