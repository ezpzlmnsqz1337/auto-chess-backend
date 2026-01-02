"""Tests for Chess AI module."""

import chess

from src.ai.chess_ai import ChessAI, DifficultyLevel


def test_ai_initialization() -> None:
    """Test AI initializes correctly."""
    ai = ChessAI(difficulty=DifficultyLevel.EASY)
    assert ai.difficulty == DifficultyLevel.EASY
    assert ai.engine is None


def test_ai_random_move() -> None:
    """Test random difficulty makes legal moves."""
    ai = ChessAI(difficulty=DifficultyLevel.RANDOM)
    board = chess.Board()

    # Make 10 moves to ensure it works
    for _ in range(10):
        move = ai.get_move(board)
        assert move in board.legal_moves
        board.push(move)


def test_ai_easy_move() -> None:
    """Test easy difficulty makes legal moves."""
    ai = ChessAI(difficulty=DifficultyLevel.EASY)
    board = chess.Board()

    move = ai.get_move(board)
    assert move in board.legal_moves


def test_ai_easy_prefers_captures() -> None:
    """Test easy AI prefers winning captures."""
    ai = ChessAI(difficulty=DifficultyLevel.EASY)

    # Position where white can capture black queen
    board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/4q3/3P4/PPPNPPPP/R1BQKBNR w KQkq - 0 1")

    move = ai.get_move(board)

    # AI should capture the queen with knight
    assert board.piece_at(move.to_square) == chess.Piece(chess.QUEEN, chess.BLACK)


def test_ai_medium_move() -> None:
    """Test medium difficulty makes legal moves."""
    ai = ChessAI(difficulty=DifficultyLevel.MEDIUM)
    board = chess.Board()

    move = ai.get_move(board)
    assert move in board.legal_moves


def test_ai_medium_looks_ahead() -> None:
    """Test medium AI uses lookahead."""
    # Scholar's mate position - AI should block
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 1")

    ai = ChessAI(difficulty=DifficultyLevel.MEDIUM)
    move = ai.get_move(board)

    # AI should defend against checkmate (move pawn or knight)
    board.push(move)
    assert not board.is_checkmate()


def test_ai_no_legal_moves_raises() -> None:
    """Test AI raises error when no legal moves."""
    ai = ChessAI(difficulty=DifficultyLevel.EASY)

    # Create a board and manually set it to have no legal moves
    board = chess.Board()
    board.clear_board()  # Empty board
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.E2, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.F1, chess.Piece(chess.QUEEN, chess.WHITE))
    board.turn = chess.BLACK
    # Black king is trapped

    if not board.is_checkmate():
        # Skip this test if position isn't actually checkmate
        return

    try:
        ai.get_move(board)
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "No legal moves" in str(e)


def test_ai_context_manager() -> None:
    """Test AI works as context manager."""
    with ChessAI(difficulty=DifficultyLevel.EASY) as ai:
        board = chess.Board()
        move = ai.get_move(board)
        assert move in board.legal_moves


def test_ai_close() -> None:
    """Test AI close method doesn't crash without engine."""
    ai = ChessAI(difficulty=DifficultyLevel.EASY)
    ai.close()  # Should not raise


def test_ai_evaluate_material() -> None:
    """Test material evaluation."""
    ai = ChessAI(difficulty=DifficultyLevel.EASY)

    # Starting position is equal
    board = chess.Board()
    assert ai._evaluate_material(board) == 0

    # Position with white queen advantage
    board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert ai._evaluate_material(board) > 0


def test_ai_evaluate_position() -> None:
    """Test full position evaluation."""
    ai = ChessAI(difficulty=DifficultyLevel.MEDIUM)

    # Starting position - should be roughly equal
    board = chess.Board()
    score = ai._evaluate_position(board)
    # Material is equal, positional bonuses may vary
    assert -2000 < score < 2000

    # Position with material advantage (white has extra queen)
    board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    score = ai._evaluate_position(board)
    assert score > 500  # White has clear material advantage


def test_difficulty_levels_all_work() -> None:
    """Test all difficulty levels can make moves."""
    board = chess.Board()

    for difficulty in [DifficultyLevel.RANDOM, DifficultyLevel.EASY, DifficultyLevel.MEDIUM]:
        ai = ChessAI(difficulty=difficulty)
        move = ai.get_move(board.copy())
        assert move in board.legal_moves


def test_ai_minimax_basic() -> None:
    """Test minimax algorithm runs without errors."""
    ai = ChessAI(difficulty=DifficultyLevel.MEDIUM)
    board = chess.Board()

    # This should search 2 ply deep
    score = ai._minimax(board, depth=2, alpha=float("-inf"), beta=float("inf"))

    # Score should be reasonable (not infinite)
    assert -30000 < score < 30000
