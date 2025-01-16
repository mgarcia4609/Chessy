import chess
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class EngineAnalysis:
    """Analysis results from the engine"""
    score: float                 # Total evaluation score
    material_balance: float = 0  # Pure material score
    positional_score: float = 0  # Position quality score
    mobility_score: float = 0    # Movement possibilities score
    center_control: float = 0    # Control of central squares
    king_safety: float = 0       # King safety evaluation
    depth: int = 1               # Search depth (1 for static evaluation)
    pv: List[str] = None         # Principal variation (planned moves)
    
    def __post_init__(self):
        if self.pv is None:
            self.pv = []

    def __str__(self):
        """Human readable analysis"""
        return (f"Score: {self.score:.2f} "
                f"(Material: {self.material_balance:.2f}, "
                f"Position: {self.positional_score:.2f}, "
                f"Mobility: {self.mobility_score:.2f}, "
                f"Center: {self.center_control:.2f}, "
                f"King Safety: {self.king_safety:.2f})")


class ChessEngine:
    """Simple chess engine wrapper using python-chess"""
    
    def __init__(self):
        self._board = chess.Board()
    
    def set_position(self, fen: str = None, moves: list = None):
        """Set the current position"""
        if fen:
            self._board = chess.Board(fen)
        else:
            self._board = chess.Board()
        
        if moves:
            for move in moves:
                self._board.push(chess.Move.from_uci(move))
                
    def get_legal_moves(self) -> List[str]:
        """Get list of legal moves in UCI format"""
        return [move.uci() for move in self._board.legal_moves]
    
    def make_move(self, move: str):
        """Make a move on the board"""
        self._board.push(chess.Move.from_uci(move))
        
    def evaluate_position(self) -> EngineAnalysis:
        """Sophisticated static position evaluation"""
        # Initialize component scores
        material = 0
        positional = 0
        mobility = 0
        center = 0
        king_safety = 0
        
        # More accurate piece values (in centipawns)
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000  # High value to detect mate
        }
        
        # Center squares for control evaluation
        center_squares = {chess.E4, chess.E5, chess.D4, chess.D5}
        extended_center = {
            chess.C3, chess.D3, chess.E3, chess.F3,
            chess.C4, chess.D4, chess.E4, chess.F4,
            chess.C5, chess.D5, chess.E5, chess.F5,
            chess.C6, chess.D6, chess.E6, chess.F6
        }
        
        # Calculate material and basic positional scores
        for square, piece in self._board.piece_map().items():
            value = piece_values[piece.piece_type]
            multiplier = 1 if piece.color == chess.WHITE else -1
            
            # Material score
            material += value * multiplier
            
            # Center control bonus
            if square in center_squares:
                center += 30 * multiplier  # Major bonus for center control
            elif square in extended_center:
                center += 15 * multiplier  # Minor bonus for extended center
                
            # Add potential center control for pawns that can move to center
            if piece.piece_type == chess.PAWN:
                # Get the square in front of the pawn
                next_square = square + 8 if piece.color == chess.WHITE else square - 8
                if 0 <= next_square < 64:  # Check if square is on board
                    if next_square in center_squares:
                        center += 10 * multiplier  # Bonus for potential center control
                    elif next_square in extended_center:
                        center += 5 * multiplier   # Minor bonus for potential extended center

            # Positional bonuses
            if piece.piece_type == chess.PAWN:
                # Passed pawn bonus - using bitwise operations
                file_mask = chess.BB_FILES[chess.square_file(square)]
                pawns_on_file = self._board.pawns & file_mask
                # A passed pawn has no opposing pawns ahead of it on the same file
                if piece.color == chess.WHITE:
                    # For white pawns, check squares above
                    ahead_mask = file_mask & ((1 << square) - 1)  # All squares above current square
                    if not (pawns_on_file & ahead_mask & self._board.occupied_co[chess.BLACK]):
                        positional += 50 * multiplier
                else:
                    # For black pawns, check squares below
                    ahead_mask = file_mask & ~((1 << (square + 1)) - 1)  # All squares below current square
                    if not (pawns_on_file & ahead_mask & self._board.occupied_co[chess.WHITE]):
                        positional += 50 * multiplier

                # Advanced pawn bonus
                rank = chess.square_rank(square)
                if piece.color == chess.WHITE:
                    # Bonus only for advancing beyond rank 2
                    if rank > 1:  # pawns start on rank 2
                        positional += (rank - 1) * 10 * multiplier
                else:
                    # Bonus only for advancing beyond rank 7
                    if rank < 6:  # pawns start on rank 7
                        positional += (6 - rank) * 10 * multiplier

            elif piece.piece_type == chess.BISHOP:
                # Bishop pair bonus
                if len([p for p in self._board.pieces(chess.BISHOP, piece.color)]) == 2:
                    positional += 50 * multiplier

            elif piece.piece_type == chess.KING:
                # King safety evaluation
                if len(self._board.piece_map()) > 20:  # Middlegame
                    rank = chess.square_rank(square)
                    file = chess.square_file(square)
                    
                    # Define safe squares after castling
                    white_kingside_castle = (rank == 0 and file >= 6)  # g1, h1
                    white_queenside_castle = (rank == 0 and file <= 2)  # a1, b1, c1
                    black_kingside_castle = (rank == 7 and file >= 6)  # g8, h8
                    black_queenside_castle = (rank == 7 and file <= 2)  # a8, b8, c8
                    
                    # Award points for proper castling positions
                    if piece.color == chess.WHITE:
                        if white_kingside_castle and self._board.has_kingside_castling_rights(chess.WHITE):
                            king_safety += 100
                        elif white_queenside_castle and self._board.has_queenside_castling_rights(chess.WHITE):
                            king_safety += 100
                    else:  # Black
                        if black_kingside_castle and self._board.has_kingside_castling_rights(chess.BLACK):
                            king_safety += 100
                        elif black_queenside_castle and self._board.has_queenside_castling_rights(chess.BLACK):
                            king_safety += 100
                    
                    # Penalize kings in the center
                    center_files = [3, 4]  # d and e files
                    if file in center_files:
                        king_safety -= 50 * multiplier
        
        # Mobility evaluation
        for square in chess.SQUARES:
            piece = self._board.piece_at(square)
            if piece:
                mobility_value = len(self._board.attacks(square))
                mobility += mobility_value * (1 if piece.color == chess.WHITE else -1)
        
        # Normalize mobility score
        mobility = mobility * 0.1
        
        # Calculate final score
        total_score = (material / 100.0 +  # Convert centipawns to pawns
                      positional / 100.0 +
                      mobility +
                      center / 100.0 +
                      king_safety / 100.0)
        
        return EngineAnalysis(
            score=total_score,
            material_balance=material / 100.0,
            positional_score=positional / 100.0,
            mobility_score=mobility,
            center_control=center / 100.0,
            king_safety=king_safety / 100.0
        )
    
    def get_attacked_squares(self, square: chess.Square) -> chess.SquareSet:
        """Get squares that can be legally attacked by piece at given square.
        This excludes squares occupied by friendly pieces but includes squares with enemy pieces."""
        piece = self._board.piece_at(square)
        if not piece:
            return chess.SquareSet()
            
        attacks = self._board.attacks(square)
        # Remove squares occupied by friendly pieces
        friendly_pieces = self._board.occupied_co[piece.color]
        return attacks & ~friendly_pieces  # Bitwise operations to exclude friendly pieces
    
    def get_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        """Get piece at given square"""
        return self._board.piece_at(square)
    
    def get_piece_map(self) -> Dict[chess.Square, chess.Piece]:
        """Get map of all pieces on the board"""
        return self._board.piece_map()
    
    def is_attacked_by(self, color: bool, square: chess.Square) -> bool:
        """Check if square is attacked by given color"""
        return self._board.is_attacked_by(color, square)
    
    def get_turn(self) -> bool:
        """Get current side to move (True for white, False for black)"""
        return self._board.turn
    
    def parse_square(self, square: str) -> chess.Square:
        """Parse a square from a string"""
        return chess.parse_square(square)
    
    def square_file(self, square: chess.Square) -> int:
        """Get the file index of a square"""
        return chess.square_file(square)
    
    def square_rank(self, square: chess.Square) -> int:
        """Get the rank index of a square"""
        return chess.square_rank(square)
    
    def get_potential_attacks(self, square: chess.Square) -> chess.SquareSet:
        """Get all squares that could be attacked by piece at given square, regardless of legality.
        This includes squares occupied by friendly pieces and moves that might not be legal due to pins or checks."""
        return self._board.attacks(square)
