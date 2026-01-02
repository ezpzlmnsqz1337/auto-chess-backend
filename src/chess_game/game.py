"""
Chess game engine with full rule validation.

Implements the rules of chess including:
- All piece movement rules (pawn, knight, bishop, rook, queen, king)
- Capture detection
- Check and checkmate detection
- Castling (kingside and queenside)
- En passant capture
- Pawn promotion
- Game state management
"""

from chess_game.piece import Piece, PieceType
from chess_game.player import Player
from chess_game.square import Square


class ChessGame:
    """
    Chess game engine with full rule validation.

    Tracks the current board state, whose turn it is, and validates all moves
    according to standard chess rules.
    """

    def __init__(self) -> None:
        """Initialize a new chess game with standard starting position."""
        self.board: dict[Square, Piece] = {}
        self.current_player = Player.WHITE
        self.en_passant_target: Square | None = None  # Square where en passant can capture
        self.halfmove_clock = 0  # For fifty-move rule (not enforced yet)
        self.fullmove_number = 1  # Increments after black's move
        self._setup_standard_position()

    def _setup_standard_position(self) -> None:
        """Set up pieces in standard chess starting position."""
        # White pieces (rows 0-1)
        for col in range(8):
            self.board[Square(1, col)] = Piece(PieceType.PAWN, Player.WHITE)

        self.board[Square(0, 0)] = Piece(PieceType.ROOK, Player.WHITE)
        self.board[Square(0, 1)] = Piece(PieceType.KNIGHT, Player.WHITE)
        self.board[Square(0, 2)] = Piece(PieceType.BISHOP, Player.WHITE)
        self.board[Square(0, 3)] = Piece(PieceType.QUEEN, Player.WHITE)
        self.board[Square(0, 4)] = Piece(PieceType.KING, Player.WHITE)
        self.board[Square(0, 5)] = Piece(PieceType.BISHOP, Player.WHITE)
        self.board[Square(0, 6)] = Piece(PieceType.KNIGHT, Player.WHITE)
        self.board[Square(0, 7)] = Piece(PieceType.ROOK, Player.WHITE)

        # Black pieces (rows 6-7)
        for col in range(8):
            self.board[Square(6, col)] = Piece(PieceType.PAWN, Player.BLACK)

        self.board[Square(7, 0)] = Piece(PieceType.ROOK, Player.BLACK)
        self.board[Square(7, 1)] = Piece(PieceType.KNIGHT, Player.BLACK)
        self.board[Square(7, 2)] = Piece(PieceType.BISHOP, Player.BLACK)
        self.board[Square(7, 3)] = Piece(PieceType.QUEEN, Player.BLACK)
        self.board[Square(7, 4)] = Piece(PieceType.KING, Player.BLACK)
        self.board[Square(7, 5)] = Piece(PieceType.BISHOP, Player.BLACK)
        self.board[Square(7, 6)] = Piece(PieceType.KNIGHT, Player.BLACK)
        self.board[Square(7, 7)] = Piece(PieceType.ROOK, Player.BLACK)

    def get_piece(self, square: Square) -> Piece | None:
        """Get the piece at a square, or None if empty."""
        return self.board.get(square)

    def is_square_attacked(self, square: Square, by_player: Player) -> bool:
        """Check if a square is attacked by any piece of the given player."""
        for from_square, piece in self.board.items():
            if piece.player != by_player:
                continue

            # Check if this piece can attack the target square
            # Use _get_pseudo_legal_moves which doesn't check for king safety
            moves = self._get_pseudo_legal_moves(from_square)
            if square in moves:
                return True

        return False

    def is_in_check(self, player: Player) -> bool:
        """Check if the given player's king is in check."""
        # Find the king
        king_square = None
        for square, piece in self.board.items():
            if piece.piece_type == PieceType.KING and piece.player == player:
                king_square = square
                break

        if king_square is None:
            return False  # No king found (shouldn't happen in valid game)

        # Check if any opponent piece attacks the king's square
        return self.is_square_attacked(king_square, player.opposite())

    def _get_pseudo_legal_moves(self, from_square: Square) -> list[Square]:
        """
        Get all pseudo-legal moves (doesn't check if king is left in check).

        This is used for move generation and attack detection.
        """
        piece = self.get_piece(from_square)
        if piece is None:
            return []

        if piece.piece_type == PieceType.PAWN:
            return self._get_pawn_moves(from_square, piece)
        elif piece.piece_type == PieceType.KNIGHT:
            return self._get_knight_moves(from_square, piece)
        elif piece.piece_type == PieceType.BISHOP:
            return self._get_bishop_moves(from_square, piece)
        elif piece.piece_type == PieceType.ROOK:
            return self._get_rook_moves(from_square, piece)
        elif piece.piece_type == PieceType.QUEEN:
            return self._get_queen_moves(from_square, piece)
        elif piece.piece_type == PieceType.KING:
            return self._get_king_moves(from_square, piece)

        return []

    def get_legal_moves(self, from_square: Square) -> list[Square]:
        """
        Get all legal moves for a piece at the given square.

        Filters out moves that would leave the king in check.
        Adds castling for kings.
        """
        piece = self.get_piece(from_square)
        if piece is None or piece.player != self.current_player:
            return []

        pseudo_legal = self._get_pseudo_legal_moves(from_square)
        legal = []

        for to_square in pseudo_legal:
            # Try the move and see if it leaves the king in check
            if self._is_legal_move_without_check(from_square, to_square):
                legal.append(to_square)

        # Add castling for kings (done separately to avoid recursion in pseudo-legal move generation)
        if (
            piece.piece_type == PieceType.KING
            and not piece.has_moved
            and not self.is_in_check(piece.player)
        ):
            # Kingside castling
            kingside_rook_square = Square(from_square.row, 7)
            kingside_rook = self.get_piece(kingside_rook_square)
            if (
                kingside_rook is not None
                and kingside_rook.piece_type == PieceType.ROOK
                and not kingside_rook.has_moved
                and self.get_piece(Square(from_square.row, 5)) is None
                and self.get_piece(Square(from_square.row, 6)) is None
                and not self.is_square_attacked(Square(from_square.row, 5), piece.player.opposite())
                and not self.is_square_attacked(Square(from_square.row, 6), piece.player.opposite())
            ):
                legal.append(Square(from_square.row, 6))  # King moves to g-file

            # Queenside castling
            queenside_rook_square = Square(from_square.row, 0)
            queenside_rook = self.get_piece(queenside_rook_square)
            if (
                queenside_rook is not None
                and queenside_rook.piece_type == PieceType.ROOK
                and not queenside_rook.has_moved
                and self.get_piece(Square(from_square.row, 1)) is None
                and self.get_piece(Square(from_square.row, 2)) is None
                and self.get_piece(Square(from_square.row, 3)) is None
                and not self.is_square_attacked(Square(from_square.row, 3), piece.player.opposite())
                and not self.is_square_attacked(Square(from_square.row, 2), piece.player.opposite())
            ):
                legal.append(Square(from_square.row, 2))  # King moves to c-file

        return legal

    def _is_legal_move_without_check(self, from_square: Square, to_square: Square) -> bool:
        """Check if a move is legal (doesn't leave king in check)."""
        # Save state
        piece = self.board[from_square]
        captured = self.board.get(to_square)
        old_en_passant = self.en_passant_target

        # Make the move temporarily
        self.board[to_square] = piece
        del self.board[from_square]

        # Handle en passant capture (remove captured pawn)
        if piece.piece_type == PieceType.PAWN and to_square == old_en_passant:
            capture_row = from_square.row
            captured_pawn_square = Square(capture_row, to_square.col)
            captured_pawn = self.board.pop(captured_pawn_square, None)
        else:
            captured_pawn = None

        # Check if king is in check
        is_legal = not self.is_in_check(piece.player)

        # Undo the move
        self.board[from_square] = piece
        if captured is not None:
            self.board[to_square] = captured
        else:
            del self.board[to_square]

        if captured_pawn is not None:
            capture_row = from_square.row
            self.board[Square(capture_row, to_square.col)] = captured_pawn

        self.en_passant_target = old_en_passant

        return is_legal

    def _get_pawn_moves(self, from_square: Square, piece: Piece) -> list[Square]:
        """Get all pseudo-legal pawn moves."""
        moves = []
        direction = 1 if piece.player == Player.WHITE else -1
        start_row = 1 if piece.player == Player.WHITE else 6

        # Forward move
        forward_row = from_square.row + direction
        if 0 <= forward_row < 8:
            forward_square = Square(forward_row, from_square.col)
            if self.get_piece(forward_square) is None:
                moves.append(forward_square)

                # Double move from starting position
                if from_square.row == start_row:
                    double_row = from_square.row + 2 * direction
                    double_square = Square(double_row, from_square.col)
                    if self.get_piece(double_square) is None:
                        moves.append(double_square)

        # Captures (diagonal)
        for col_offset in [-1, 1]:
            capture_row = from_square.row + direction
            capture_col = from_square.col + col_offset
            if 0 <= capture_row < 8 and 0 <= capture_col < 8:
                capture_square = Square(capture_row, capture_col)
                target = self.get_piece(capture_square)
                if target is not None and target.player != piece.player:
                    moves.append(capture_square)

                # En passant
                if capture_square == self.en_passant_target:
                    moves.append(capture_square)

        return moves

    def _get_knight_moves(self, from_square: Square, piece: Piece) -> list[Square]:
        """Get all pseudo-legal knight moves."""
        moves = []
        knight_offsets = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]

        for row_offset, col_offset in knight_offsets:
            target_row = from_square.row + row_offset
            target_col = from_square.col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                target_square = Square(target_row, target_col)
                target = self.get_piece(target_square)
                if target is None or target.player != piece.player:
                    moves.append(target_square)

        return moves

    def _get_sliding_moves(
        self, from_square: Square, piece: Piece, directions: list[tuple[int, int]]
    ) -> list[Square]:
        """Get moves for sliding pieces (bishop, rook, queen)."""
        moves = []

        for row_dir, col_dir in directions:
            current_row = from_square.row
            current_col = from_square.col

            while True:
                current_row += row_dir
                current_col += col_dir

                if not (0 <= current_row < 8 and 0 <= current_col < 8):
                    break

                target_square = Square(current_row, current_col)
                target = self.get_piece(target_square)

                if target is None:
                    moves.append(target_square)
                else:
                    if target.player != piece.player:
                        moves.append(target_square)
                    break

        return moves

    def _get_bishop_moves(self, from_square: Square, piece: Piece) -> list[Square]:
        """Get all pseudo-legal bishop moves."""
        diagonals = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._get_sliding_moves(from_square, piece, diagonals)

    def _get_rook_moves(self, from_square: Square, piece: Piece) -> list[Square]:
        """Get all pseudo-legal rook moves."""
        orthogonals = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_sliding_moves(from_square, piece, orthogonals)

    def _get_queen_moves(self, from_square: Square, piece: Piece) -> list[Square]:
        """Get all pseudo-legal queen moves (combination of rook and bishop)."""
        all_directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        return self._get_sliding_moves(from_square, piece, all_directions)

    def _get_king_moves(self, from_square: Square, piece: Piece) -> list[Square]:
        """Get all pseudo-legal king moves (NOT including castling - that's added in get_legal_moves)."""
        moves = []

        # Normal king moves (one square in any direction)
        for row_offset in [-1, 0, 1]:
            for col_offset in [-1, 0, 1]:
                if row_offset == 0 and col_offset == 0:
                    continue

                target_row = from_square.row + row_offset
                target_col = from_square.col + col_offset
                if 0 <= target_row < 8 and 0 <= target_col < 8:
                    target_square = Square(target_row, target_col)
                    target = self.get_piece(target_square)
                    if target is None or target.player != piece.player:
                        moves.append(target_square)

        return moves

    def make_move(
        self, from_square: Square, to_square: Square, promotion: PieceType | None = None
    ) -> bool:
        """
        Make a move on the board.

        Returns True if the move was legal and executed, False otherwise.
        Handles en passant, castling, and pawn promotion.
        """
        piece = self.get_piece(from_square)
        if piece is None or piece.player != self.current_player:
            return False

        # Check if move is legal
        legal_moves = self.get_legal_moves(from_square)
        if to_square not in legal_moves:
            return False

        # Handle castling
        if piece.piece_type == PieceType.KING and abs(to_square.col - from_square.col) == 2:
            # Kingside castling
            if to_square.col == 6:
                rook_from = Square(from_square.row, 7)
                rook_to = Square(from_square.row, 5)
                rook = self.board[rook_from]
                self.board[rook_to] = rook
                del self.board[rook_from]
                rook.has_moved = True
            # Queenside castling
            elif to_square.col == 2:
                rook_from = Square(from_square.row, 0)
                rook_to = Square(from_square.row, 3)
                rook = self.board[rook_from]
                self.board[rook_to] = rook
                del self.board[rook_from]
                rook.has_moved = True

        # Handle en passant capture
        if piece.piece_type == PieceType.PAWN and to_square == self.en_passant_target:
            # Remove the captured pawn
            captured_pawn_square = Square(from_square.row, to_square.col)
            del self.board[captured_pawn_square]

        # Update en passant target for next move
        self.en_passant_target = None

        if piece.piece_type == PieceType.PAWN and abs(to_square.row - from_square.row) == 2:
            # Pawn moved two squares, set en passant target
            self.en_passant_target = Square((from_square.row + to_square.row) // 2, from_square.col)

        # Make the move
        captured = self.board.get(to_square)
        self.board[to_square] = piece
        del self.board[from_square]
        piece.has_moved = True

        # Handle pawn promotion
        if piece.piece_type == PieceType.PAWN and (
            (piece.player == Player.WHITE and to_square.row == 7)
            or (piece.player == Player.BLACK and to_square.row == 0)
        ):
            if promotion is None:
                promotion = PieceType.QUEEN  # Default to queen
            piece.piece_type = promotion

        # Update halfmove clock (for fifty-move rule)
        if piece.piece_type == PieceType.PAWN or captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Update fullmove number
        if self.current_player == Player.BLACK:
            self.fullmove_number += 1

        # Switch players
        self.current_player = self.current_player.opposite()

        return True

    def is_checkmate(self) -> bool:
        """Check if the current player is in checkmate."""
        if not self.is_in_check(self.current_player):
            return False

        # Check if any move can get out of check
        # Use list() to avoid RuntimeError from dict changing during iteration
        for square, piece in list(self.board.items()):
            if piece.player == self.current_player and len(self.get_legal_moves(square)) > 0:
                return False

        return True

    def is_stalemate(self) -> bool:
        """Check if the current player is in stalemate (no legal moves, not in check)."""
        if self.is_in_check(self.current_player):
            return False

        # Check if any legal moves exist
        # Use list() to avoid RuntimeError from dict changing during iteration
        for square, piece in list(self.board.items()):
            if piece.player == self.current_player and len(self.get_legal_moves(square)) > 0:
                return False

        return True

    def get_board_state_string(self) -> str:
        """Get a string representation of the board (for debugging/visualization)."""
        lines = []
        for row in range(7, -1, -1):  # Start from rank 8 down to rank 1
            line = f"{row + 1} "
            for col in range(8):
                piece = self.get_piece(Square(row, col))
                if piece is None:
                    line += ". "
                else:
                    line += str(piece) + " "
            lines.append(line)
        lines.append("  a b c d e f g h")
        return "\n".join(lines)
