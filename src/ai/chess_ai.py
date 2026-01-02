"""Chess AI with multiple difficulty levels and strategies."""

import random
from enum import Enum

import chess
import chess.engine


class DifficultyLevel(Enum):
    """AI difficulty levels."""

    RANDOM = "random"  # Completely random legal moves
    EASY = "easy"  # Basic piece value evaluation
    MEDIUM = "medium"  # Deeper evaluation with positional understanding
    HARD = "hard"  # Stockfish integration (requires stockfish binary)


class ChessAI:
    """Chess AI that can play at different difficulty levels."""

    # Piece values for evaluation (standard centipawn values)
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    # Piece-square tables for positional bonuses (simplified)
    # Positive values are good for white, board is from white's perspective
    PAWN_TABLE = [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    KNIGHT_TABLE = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50,
    ]

    def __init__(
        self,
        difficulty: DifficultyLevel = DifficultyLevel.EASY,
        stockfish_path: str | None = None,
    ):
        """
        Initialize Chess AI.

        Args:
            difficulty: AI difficulty level
            stockfish_path: Path to stockfish binary (required for HARD difficulty)
        """
        self.difficulty = difficulty
        self.stockfish_path = stockfish_path
        self.engine: chess.engine.SimpleEngine | None = None

        if difficulty == DifficultyLevel.HARD:
            if not stockfish_path:
                raise ValueError("stockfish_path required for HARD difficulty")
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            except Exception as e:
                raise RuntimeError(f"Failed to start Stockfish engine: {e}") from e

    def get_move(self, board: chess.Board) -> chess.Move:
        """
        Get the AI's next move for the given board position.

        Args:
            board: Current chess board state

        Returns:
            The chosen move

        Raises:
            ValueError: If no legal moves available (shouldn't happen in normal game)
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available")

        if self.difficulty == DifficultyLevel.RANDOM:
            return self._get_random_move(legal_moves)
        elif self.difficulty == DifficultyLevel.EASY:
            return self._get_easy_move(board, legal_moves)
        elif self.difficulty == DifficultyLevel.MEDIUM:
            return self._get_medium_move(board, legal_moves)
        elif self.difficulty == DifficultyLevel.HARD:
            return self._get_hard_move(board)
        else:
            return self._get_random_move(legal_moves)

    def _get_random_move(self, legal_moves: list[chess.Move]) -> chess.Move:
        """Select a completely random legal move."""
        return random.choice(legal_moves)

    def _get_easy_move(self, board: chess.Board, legal_moves: list[chess.Move]) -> chess.Move:
        """
        Select move using basic material evaluation.

        Strategy:
        1. Look for captures that win material
        2. Avoid hanging pieces
        3. Otherwise random move
        """
        best_moves: list[tuple[chess.Move, int]] = []
        best_score = float("-inf")

        for move in legal_moves:
            board.push(move)
            score = self._evaluate_material(board)
            board.pop()

            # Negate score if it's opponent's turn (we just made a move)
            if board.turn == chess.BLACK:
                score = -score

            if score > best_score:
                best_score = score
                best_moves = [(move, score)]
            elif score == best_score:
                best_moves.append((move, score))

        # Among equally good moves, prefer captures
        capture_moves = [m for m, s in best_moves if board.is_capture(m)]
        if capture_moves:
            return random.choice(capture_moves)

        return random.choice([m for m, s in best_moves])

    def _get_medium_move(
        self, board: chess.Board, legal_moves: list[chess.Move]
    ) -> chess.Move:
        """
        Select move using minimax with alpha-beta pruning.

        Strategy:
        1. Search 2-3 ply deep
        2. Use piece-square tables for positional evaluation
        3. Consider material and position
        """
        best_move = None
        best_score = float("-inf")
        alpha = float("-inf")
        beta = float("inf")

        for move in legal_moves:
            board.push(move)
            score = -self._minimax(board, depth=2, alpha=-beta, beta=-alpha)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move if best_move else random.choice(legal_moves)

    def _get_hard_move(self, board: chess.Board) -> chess.Move:
        """
        Use Stockfish engine for best move.

        Args:
            board: Current board state

        Returns:
            Best move according to Stockfish
        """
        if not self.engine:
            raise RuntimeError("Stockfish engine not initialized")

        result = self.engine.play(board, chess.engine.Limit(time=1.0))
        if result.move is None:
            raise RuntimeError("Stockfish returned no move")
        return result.move

    def _minimax(self, board: chess.Board, depth: int, alpha: float, beta: float) -> float:
        """
        Minimax algorithm with alpha-beta pruning.

        Args:
            board: Current board state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning

        Returns:
            Evaluated score for current position
        """
        if depth == 0 or board.is_game_over():
            return self._evaluate_position(board)

        if board.turn == chess.WHITE:
            max_eval = float("-inf")
            for move in board.legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, alpha, beta)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in board.legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, alpha, beta)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate_material(self, board: chess.Board) -> int:
        """
        Evaluate board based purely on material.

        Args:
            board: Board to evaluate

        Returns:
            Score in centipawns (positive = white advantage)
        """
        score = 0
        for piece_type in [
            chess.PAWN,
            chess.KNIGHT,
            chess.BISHOP,
            chess.ROOK,
            chess.QUEEN,
        ]:
            score += len(board.pieces(piece_type, chess.WHITE)) * self.PIECE_VALUES[piece_type]
            score -= len(board.pieces(piece_type, chess.BLACK)) * self.PIECE_VALUES[piece_type]
        return score

    def _evaluate_position(self, board: chess.Board) -> float:
        """
        Evaluate board position including material and piece placement.

        Args:
            board: Board to evaluate

        Returns:
            Score in centipawns (positive = white advantage)
        """
        if board.is_checkmate():
            return -20000 if board.turn == chess.WHITE else 20000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = self._evaluate_material(board)

        # Add positional bonuses
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            # Get piece-square table value
            table_value = 0
            if piece.piece_type == chess.PAWN:
                table_value = self.PAWN_TABLE[square]
            elif piece.piece_type == chess.KNIGHT:
                table_value = self.KNIGHT_TABLE[square]

            # Flip table for black pieces
            if piece.color == chess.BLACK:
                table_value = -self.PAWN_TABLE[chess.square_mirror(square)]

            score += table_value if piece.color == chess.WHITE else -table_value

        return score

    def close(self) -> None:
        """Close the chess engine if running."""
        if self.engine:
            self.engine.quit()
            self.engine = None

    def __enter__(self) -> "ChessAI":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Context manager exit."""
        self.close()
