"""
Tests for chess game logic with visualizations.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from chess_game import ChessGame, Piece, PieceType, Player, Square
from tests.visualization import setup_chess_board_plot, standard_draw_chess_pieces

# Create output directory for visualizations
OUTPUT_DIR = Path(__file__).parent / "output" / "chess"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _draw_chess_board(
    game: ChessGame,
    title: str,
    highlighted_squares: dict[Square, tuple[int, int, int]] | None = None,
    show_legal_moves: Square | None = None,
) -> Figure:
    """Draw a chess board with pieces and optional highlights using standardized plots."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Use standardized chess board setup
    setup_chess_board_plot(ax, title=title, show_coordinates=True)

    # Highlight squares (custom for this test)
    if highlighted_squares:
        for square, color_rgb in highlighted_squares.items():
            color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
            ax.add_patch(
                mpatches.Rectangle(
                    (square.col, square.row),
                    1,
                    1,
                    facecolor=color_hex,
                    edgecolor="red",
                    linewidth=2,
                    alpha=0.7,
                    zorder=5,
                )
            )

    # Show legal moves if requested (custom for this test)
    if show_legal_moves:
        legal_moves = game.get_legal_moves(show_legal_moves)
        for move_square in legal_moves:
            # Draw green circle for legal moves
            circle = mpatches.Circle(
                (move_square.col + 0.5, move_square.row + 0.5),
                0.15,
                facecolor="green",
                alpha=0.7,
                zorder=15,
            )
            ax.add_patch(circle)

    # Draw pieces using standardized function
    standard_draw_chess_pieces(ax, game)

    return fig


def test_initial_position() -> None:
    """Test that the game starts with standard chess position."""
    game = ChessGame()

    # Check white pieces
    e1_piece = game.get_piece(Square.from_notation("e1"))
    assert e1_piece is not None and e1_piece.piece_type == PieceType.KING
    d1_piece = game.get_piece(Square.from_notation("d1"))
    assert d1_piece is not None and d1_piece.piece_type == PieceType.QUEEN
    a1_piece = game.get_piece(Square.from_notation("a1"))
    assert a1_piece is not None and a1_piece.piece_type == PieceType.ROOK
    b1_piece = game.get_piece(Square.from_notation("b1"))
    assert b1_piece is not None and b1_piece.piece_type == PieceType.KNIGHT
    c1_piece = game.get_piece(Square.from_notation("c1"))
    assert c1_piece is not None and c1_piece.piece_type == PieceType.BISHOP

    # Check black pieces
    e8_piece = game.get_piece(Square.from_notation("e8"))
    assert e8_piece is not None and e8_piece.piece_type == PieceType.KING
    d8_piece = game.get_piece(Square.from_notation("d8"))
    assert d8_piece is not None and d8_piece.piece_type == PieceType.QUEEN

    # Check pawns
    for file in "abcdefgh":
        pawn2 = game.get_piece(Square.from_notation(f"{file}2"))
        assert pawn2 is not None and pawn2.piece_type == PieceType.PAWN
        pawn7 = game.get_piece(Square.from_notation(f"{file}7"))
        assert pawn7 is not None and pawn7.piece_type == PieceType.PAWN

    # Check empty squares
    for file in "abcdefgh":
        for rank in "3456":
            assert game.get_piece(Square.from_notation(f"{file}{rank}")) is None

    assert game.current_player == Player.WHITE


def test_visualize_starting_position() -> None:
    """Generate a visualization of the starting chess position."""
    game = ChessGame()

    fig = _draw_chess_board(game, "Chess Starting Position")
    fig.savefig(OUTPUT_DIR / "chess_starting_position.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def test_pawn_moves() -> None:
    """Test pawn movement rules."""
    game = ChessGame()

    # White pawn can move 1 or 2 squares forward from starting position
    e2_pawn_moves = game.get_legal_moves(Square.from_notation("e2"))
    assert Square.from_notation("e3") in e2_pawn_moves
    assert Square.from_notation("e4") in e2_pawn_moves
    assert len(e2_pawn_moves) == 2

    # Move pawn forward
    assert game.make_move(Square.from_notation("e2"), Square.from_notation("e4"))

    # After moving, black's turn
    assert game.current_player == Player.BLACK


def test_knight_moves() -> None:
    """Test knight movement in L-shape."""
    game = ChessGame()

    # White knight on b1 can move to a3 or c3
    b1_knight_moves = game.get_legal_moves(Square.from_notation("b1"))
    assert Square.from_notation("a3") in b1_knight_moves
    assert Square.from_notation("c3") in b1_knight_moves
    assert len(b1_knight_moves) == 2


def test_visualize_knight_moves() -> None:
    """Visualize legal knight moves from starting position."""
    game = ChessGame()

    knight_square = Square.from_notation("b1")
    fig = _draw_chess_board(
        game, "White Knight Legal Moves from b1", show_legal_moves=knight_square
    )

    # Highlight the knight
    highlights = {knight_square: (100, 100, 255)}  # Blue highlight
    for square, color in highlights.items():
        color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        ax = fig.gca()
        ax.add_patch(
            mpatches.Rectangle(
                (square.col, square.row), 1, 1, facecolor=color_hex, alpha=0.3, edgecolor="blue"
            )
        )

    fig.savefig(OUTPUT_DIR / "chess_knight_moves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def test_pawn_capture() -> None:
    """Test that pawns can capture diagonally."""
    game = ChessGame()

    # Move white pawn to e4
    game.make_move(Square.from_notation("e2"), Square.from_notation("e4"))
    # Move black pawn to d5
    game.make_move(Square.from_notation("d7"), Square.from_notation("d5"))
    # White pawn can now capture on d5
    e4_pawn_moves = game.get_legal_moves(Square.from_notation("e4"))
    assert Square.from_notation("d5") in e4_pawn_moves

    # Capture
    assert game.make_move(Square.from_notation("e4"), Square.from_notation("d5"))

    # Pawn should be on d5, black pawn removed
    d5_piece = game.get_piece(Square.from_notation("d5"))
    assert d5_piece is not None
    assert d5_piece.piece_type == PieceType.PAWN
    assert d5_piece.player == Player.WHITE


def test_en_passant() -> None:
    """Test en passant capture."""
    game = ChessGame()

    # Setup: White pawn on e5, black pawn moves from d7 to d5
    game.make_move(Square.from_notation("e2"), Square.from_notation("e4"))
    game.make_move(
        Square.from_notation("a7"), Square.from_notation("a6")
    )  # Black moves something else
    game.make_move(Square.from_notation("e4"), Square.from_notation("e5"))
    game.make_move(
        Square.from_notation("d7"), Square.from_notation("d5")
    )  # Black pawn moves 2 squares

    # White pawn on e5 should be able to capture en passant on d6
    e5_moves = game.get_legal_moves(Square.from_notation("e5"))
    assert Square.from_notation("d6") in e5_moves

    # Execute en passant
    assert game.make_move(Square.from_notation("e5"), Square.from_notation("d6"))

    # White pawn should be on d6, black pawn on d5 should be removed
    d6_piece = game.get_piece(Square.from_notation("d6"))
    assert d6_piece is not None
    assert d6_piece.piece_type == PieceType.PAWN
    assert d6_piece.player == Player.WHITE
    assert game.get_piece(Square.from_notation("d5")) is None


def test_castling_kingside() -> None:
    """Test kingside castling."""
    game = ChessGame()

    # Clear squares between king and rook
    del game.board[Square.from_notation("f1")]
    del game.board[Square.from_notation("g1")]

    # King should be able to castle kingside
    king_moves = game.get_legal_moves(Square.from_notation("e1"))
    assert Square.from_notation("g1") in king_moves

    # Castle
    assert game.make_move(Square.from_notation("e1"), Square.from_notation("g1"))

    # King should be on g1, rook should be on f1
    g1_piece = game.get_piece(Square.from_notation("g1"))
    assert g1_piece is not None and g1_piece.piece_type == PieceType.KING
    f1_piece = game.get_piece(Square.from_notation("f1"))
    assert f1_piece is not None and f1_piece.piece_type == PieceType.ROOK


def test_castling_queenside() -> None:
    """Test queenside castling."""
    game = ChessGame()

    # Clear squares between king and rook
    del game.board[Square.from_notation("b1")]
    del game.board[Square.from_notation("c1")]
    del game.board[Square.from_notation("d1")]

    # King should be able to castle queenside
    king_moves = game.get_legal_moves(Square.from_notation("e1"))
    assert Square.from_notation("c1") in king_moves

    # Castle
    assert game.make_move(Square.from_notation("e1"), Square.from_notation("c1"))

    # King should be on c1, rook should be on d1
    c1_piece = game.get_piece(Square.from_notation("c1"))
    assert c1_piece is not None and c1_piece.piece_type == PieceType.KING
    d1_piece = game.get_piece(Square.from_notation("d1"))
    assert d1_piece is not None and d1_piece.piece_type == PieceType.ROOK


def test_check_detection() -> None:
    """Test that check is properly detected."""
    # Create a new game with simplified position
    game = ChessGame()
    # Clear the board except kings
    game.board = {}

    game.board[Square.from_notation("e1")] = Piece(PieceType.KING, Player.WHITE)
    game.board[Square.from_notation("e8")] = Piece(PieceType.KING, Player.BLACK)

    # Add white rook threatening black king
    game.board[Square.from_notation("e5")] = Piece(PieceType.ROOK, Player.WHITE)

    # Black should be in check
    assert game.is_in_check(Player.BLACK)


def test_visualize_check() -> None:
    """Visualize a check position."""
    game = ChessGame()
    game.board = {}

    # Simple check scenario: White rook checking black king
    game.board[Square.from_notation("e1")] = Piece(PieceType.KING, Player.WHITE)
    game.board[Square.from_notation("e8")] = Piece(PieceType.KING, Player.BLACK)
    game.board[Square.from_notation("e5")] = Piece(PieceType.ROOK, Player.WHITE)
    game.current_player = Player.BLACK

    # Highlight the checking piece and king
    highlights = {
        Square.from_notation("e8"): (255, 0, 0),  # Red for king in check
        Square.from_notation("e5"): (255, 100, 0),  # Orange for attacking rook
    }

    fig = _draw_chess_board(game, "Check: White Rook Attacks Black King", highlights)
    fig.savefig(OUTPUT_DIR / "chess_check_position.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def test_cannot_move_into_check() -> None:
    """Test that king cannot move into check."""
    game = ChessGame()
    game.board = {}

    # King on e1, enemy rook on e3
    game.board[Square.from_notation("e1")] = Piece(PieceType.KING, Player.WHITE)
    game.board[Square.from_notation("e3")] = Piece(PieceType.ROOK, Player.BLACK)
    game.current_player = Player.WHITE

    # King should not be able to move to e2 (still in check from rook)
    king_moves = game.get_legal_moves(Square.from_notation("e1"))
    assert Square.from_notation("e2") not in king_moves


def test_scholar_mate() -> None:
    """Test Scholar's Mate (4-move checkmate)."""
    game = ChessGame()

    # 1. e4 e5
    game.make_move(Square.from_notation("e2"), Square.from_notation("e4"))
    game.make_move(Square.from_notation("e7"), Square.from_notation("e5"))

    # 2. Bc4 Nc6
    game.make_move(Square.from_notation("f1"), Square.from_notation("c4"))
    game.make_move(Square.from_notation("b8"), Square.from_notation("c6"))

    # 3. Qh5 Nf6
    game.make_move(Square.from_notation("d1"), Square.from_notation("h5"))
    game.make_move(Square.from_notation("g8"), Square.from_notation("f6"))

    # 4. Qxf7# (checkmate)
    assert game.make_move(Square.from_notation("h5"), Square.from_notation("f7"))

    # Black should be in checkmate
    assert game.is_checkmate()


def test_visualize_scholar_mate() -> None:
    """Visualize Scholar's Mate checkmate position."""
    game = ChessGame()

    # Execute Scholar's Mate
    game.make_move(Square.from_notation("e2"), Square.from_notation("e4"))
    game.make_move(Square.from_notation("e7"), Square.from_notation("e5"))
    game.make_move(Square.from_notation("f1"), Square.from_notation("c4"))
    game.make_move(Square.from_notation("b8"), Square.from_notation("c6"))
    game.make_move(Square.from_notation("d1"), Square.from_notation("h5"))
    game.make_move(Square.from_notation("g8"), Square.from_notation("f6"))
    game.make_move(Square.from_notation("h5"), Square.from_notation("f7"))

    # Highlight checkmate
    highlights = {
        Square.from_notation("f7"): (255, 0, 0),  # Red for checkmating queen
        Square.from_notation("e8"): (200, 0, 0),  # Dark red for checkmated king
    }

    fig = _draw_chess_board(game, "Scholar's Mate - Checkmate!", highlights)
    fig.savefig(OUTPUT_DIR / "chess_scholars_mate.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def test_stalemate() -> None:
    """Test stalemate detection."""
    game = ChessGame()
    game.board = {}

    # Stalemate position: Black king on a8, white king on c7, white queen on b6
    # Black has no legal moves but is not in check
    game.board[Square.from_notation("a8")] = Piece(PieceType.KING, Player.BLACK)
    game.board[Square.from_notation("c7")] = Piece(PieceType.KING, Player.WHITE)
    game.board[Square.from_notation("b6")] = Piece(PieceType.QUEEN, Player.WHITE)
    game.current_player = Player.BLACK

    # Black should not be in check
    assert not game.is_in_check(Player.BLACK)

    # But black has no legal moves
    assert game.is_stalemate()


def test_piece_movement_bishop() -> None:
    """Test bishop diagonal movement."""
    game = ChessGame()

    # Clear some pawns to let bishop move
    del game.board[Square.from_notation("d2")]
    del game.board[Square.from_notation("e2")]

    # Bishop should be able to move diagonally
    bishop_moves = game.get_legal_moves(Square.from_notation("c1"))
    assert Square.from_notation("d2") in bishop_moves
    assert Square.from_notation("e3") in bishop_moves
    assert Square.from_notation("f4") in bishop_moves


def test_piece_movement_rook() -> None:
    """Test rook orthogonal movement."""
    game = ChessGame()

    # Clear pawns
    del game.board[Square.from_notation("a2")]

    # Rook should be able to move vertically
    rook_moves = game.get_legal_moves(Square.from_notation("a1"))
    assert Square.from_notation("a2") in rook_moves
    assert Square.from_notation("a3") in rook_moves


def test_piece_movement_queen() -> None:
    """Test queen moves in all directions."""
    game = ChessGame()
    game.board = {}

    # Place queen in the middle
    game.board[Square.from_notation("d4")] = Piece(PieceType.QUEEN, Player.WHITE)
    game.board[Square.from_notation("a1")] = Piece(PieceType.KING, Player.WHITE)
    game.board[Square.from_notation("h8")] = Piece(PieceType.KING, Player.BLACK)
    game.current_player = Player.WHITE

    # Queen should be able to move in all 8 directions
    queen_moves = game.get_legal_moves(Square.from_notation("d4"))

    # Check some moves in each direction
    assert Square.from_notation("d8") in queen_moves  # Up
    assert Square.from_notation("d1") in queen_moves  # Down
    assert Square.from_notation("a4") in queen_moves  # Left
    assert Square.from_notation("h4") in queen_moves  # Right
    assert Square.from_notation("a7") in queen_moves  # Diagonal up-left
    assert Square.from_notation("h8") in queen_moves  # Diagonal up-right (capture)
    # Note: a1 has white king, so queen can't go there


def test_invalid_moves() -> None:
    """Test that invalid moves are rejected."""
    game = ChessGame()

    # Can't move opponent's piece
    assert not game.make_move(Square.from_notation("e7"), Square.from_notation("e5"))

    # Can't move to square occupied by own piece
    assert not game.make_move(Square.from_notation("b1"), Square.from_notation("d2"))

    # Can't move piece in invalid way (pawn moving sideways)
    assert not game.make_move(Square.from_notation("e2"), Square.from_notation("f2"))


def test_square_notation_conversion() -> None:
    """Test square notation conversion."""
    square = Square.from_notation("e4")
    assert square.row == 3
    assert square.col == 4
    assert square.to_notation() == "e4"

    square2 = Square(0, 0)
    assert square2.to_notation() == "a1"

    square3 = Square(7, 7)
    assert square3.to_notation() == "h8"
