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


@dataclass
class MoveContext:
    """Detailed chess context for a move"""
    is_capture: bool
    is_check: bool
    is_castle: bool
    piece_type: str
    captured_piece_type: Optional[str]
    source_square: str
    target_square: str
    is_promotion: bool
    promotion_piece_type: Optional[str]
    is_en_passant: bool
    gives_discovered_attack: bool
    is_blocking: bool  # Whether this move blocks enemy attacks


class ChessEngine:
    """Simple chess engine wrapper using python-chess"""
    
    def __init__(self):
        self._board = chess.Board()
    
    def set_position(self, fen: str = None, moves: list = None):
        """Set the current position"""
        if fen: # If we get a FEN string, use it directly
            self._board = chess.Board(fen)
        else: # Otherwise, we assume a starting position and need to make moves
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

    def square(self, file: int, rank: int) -> chess.Square:
        """Get the square at given file and rank"""
        return chess.square(file, rank)

    def analyze_move_context(self, move: str) -> MoveContext:
        """Analyze chess-specific implications of a move"""
        # Parse move
        source_square = move[:2]
        target_square = move[2:4]
        promotion_piece = move[4] if len(move) > 4 else None

        # Store current position
        before = self._board.copy()
        chess_move = chess.Move.from_uci(move)
        
        # Get piece info before move
        piece = before.piece_at(chess.parse_square(source_square))
        captured = before.piece_at(chess.parse_square(target_square))
        
        # Make move to analyze resulting position
        self._board.push(chess_move)
        
        context = MoveContext(
            is_capture=before.is_capture(chess_move),
            is_check=self._board.is_check(),
            is_castle=before.is_castling(chess_move),
            piece_type=piece.symbol() if piece else '',
            captured_piece_type=captured.symbol() if captured else None,
            source_square=source_square,
            target_square=target_square,
            is_promotion=chess_move.promotion is not None,
            promotion_piece_type=chess.piece_name(chess_move.promotion) if chess_move.promotion else None,
            is_en_passant=before.is_en_passant(chess_move),
            gives_discovered_attack=self._check_discovered_attacks(before, chess_move),
            is_blocking=self._check_blocked_attacks(before, chess_move)
        )
        
        # Restore position
        self._board.pop()
        return context
        
    def _check_discovered_attacks(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if move reveals any discovered attacks
        
        A discovered attack occurs when moving a piece reveals an attack
        from a different piece that was previously blocked.
        """
        from_square = move.from_square
        to_square = move.to_square
        
        # Get all our pieces except the one that's moving
        our_pieces = {
            square: piece for square, piece in position.piece_map().items()
            if piece.color == position.turn and square != from_square
        }
        
        # Get all enemy pieces
        enemy_pieces = {
            square: piece for square, piece in position.piece_map().items()
            if piece.color != position.turn
        }
        
        # For each of our pieces, check if it gains new attacks after the move
        for our_square, our_piece in our_pieces.items():
            # Skip non-sliding pieces (only sliding pieces can have discovered attacks)
            if our_piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                continue
                
            # Get attacked squares before the move
            before_squares = chess.SquareSet(position.attacks(our_square))
            
            # Make the move and get new attacked squares
            position.push(move)
            after_squares = chess.SquareSet(position.attacks(our_square))
            position.pop()
            
            # Find newly attacked squares
            new_squares = after_squares - before_squares
            
            # Check if any enemy pieces are in newly attacked squares
            for enemy_square in enemy_pieces:
                if enemy_square in new_squares:
                    return True
                    
        return False

    def _check_blocked_attacks(self, position: chess.Board, move: chess.Move) -> bool:
        """Check if move blocks any enemy attacks
        
        This is similar to discovered attacks but from the enemy's perspective - 
        we check if any enemy pieces lose attacks after our move.
        """
        to_square = move.to_square
        
        # Get all enemy pieces
        enemy_pieces = {
            square: piece for square, piece in position.piece_map().items()
            if piece.color != position.turn
        }
        
        # For each enemy piece, check if it loses attacks after our move
        for enemy_square, enemy_piece in enemy_pieces.items():
            # Get attacked squares before the move
            before_squares = chess.SquareSet(position.attacks(enemy_square))
            
            # Make the move and get new attacked squares
            position.push(move)
            after_squares = chess.SquareSet(position.attacks(enemy_square))
            position.pop()
            
            # Find lost attack squares
            lost_squares = before_squares - after_squares
            
            # If any attacks were lost, this move is blocking
            if lost_squares:
                return True
                    
        return False

    def _can_piece_attack_along_ray(self, piece_type: chess.PieceType, dx: int, dy: int) -> bool:
        """Helper method to determine if a piece type can attack along a given direction"""
        if piece_type == chess.QUEEN:
            print(f"QUEEN can attack along {dx}, {dy}")
            return True
        if piece_type == chess.ROOK:
            return dx == 0 or dy == 0
        if piece_type == chess.BISHOP:
            return abs(dx) == abs(dy)
        return False
