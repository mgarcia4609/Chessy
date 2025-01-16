from dataclasses import dataclass, field
from typing import List, Set, TYPE_CHECKING, Dict
import chess

from chess_engine.sunfish_wrapper import ChessEngine
from debate_system.protocols import Position, MoveProposal, EngineAnalysis, PersonalityConfig, EmotionalState, Interaction

if TYPE_CHECKING:
    import chess


@dataclass
class TacticalOpportunity:
    """Represents a tactical opportunity like a fork or discovered attack"""
    type: str                                    # 'fork', 'discovered_attack', etc.
    target_squares: Set['chess.Square']          # Squares being attacked
    target_pieces: List['chess.Piece']           # Pieces being attacked
    value: float                                 # Material value of the opportunity
    description: str                             # Natural language description
    confidence: float                            # How certain we are about this opportunity (0-1)


@dataclass
class ChessPieceAgent:
    """Base class for chess piece agents"""
    engine: ChessEngine
    personality: PersonalityConfig
    emotional_state: EmotionalState
    _recent_interactions: List[Interaction] = field(default_factory=list)
    _tactical_cache: Dict[str, List[TacticalOpportunity]] = field(default_factory=dict)

    #TODO: add post init for fancier engines with more options
    # def __post_init__(self):
    #     """Initialize the engine with personality settings"""
    #     for option, value in self.personality.options.items():
    #         self.engine.set_option(option, value)
    
    def evaluate_move(self, position: Position, move: str, think_time: int = 500) -> MoveProposal:
        """Evaluate a potential move
        
        Args:
            position: Current chess position
            move: Move in UCI format (e.g. 'e2e4')
            think_time: Time to think in milliseconds
            
        Returns:
            MoveProposal with evaluation and analysis
        """
        # Set up position in engine
        self.engine.set_position(position.fen, position.move_history)
        
        # Make the move
        self.engine.make_move(move)
        
        # Analyze the position after the move
        analyses = self.engine.evaluate_position()
        
        if not analyses:
            return None
            
        # Calculate weighted score based on personality
        weighted_score = self._calculate_weighted_score(analyses)
        
        # Generate argument based on personality and analysis
        argument = self._generate_argument(position, move, analyses)
        
        return MoveProposal(
            move=move,
            score=weighted_score,
            analysis=analyses,
            argument=argument
        )
    
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Calculate weighted score based on personality
        
        This is where different piece personalities can emphasize different aspects
        of the position (tactical vs positional, risk vs safety, etc)
        """
        # Tactical component includes material and mobility
        tactical_score = (analysis.material_balance + analysis.mobility_score) * self.personality.tactical_weight
        
        # Positional component includes position quality, center control, and king safety
        positional_score = (
            analysis.positional_score + 
            analysis.center_control + 
            analysis.king_safety
        ) * self.personality.positional_weight
        
        # Combine scores
        base_score = tactical_score + positional_score
        
        # Risk adjustment based on personality
        risk_factor = 1.0
        if base_score > 0:
            # Winning positions - aggressive personalities push harder
            risk_factor += (self.personality.risk_tolerance - 0.5) * 0.2  # Reduced from 0.5
        else:
            # Losing positions - cautious personalities defend harder
            risk_factor += (0.5 - self.personality.risk_tolerance) * 0.2  # Reduced from 0.5
            
        return base_score * risk_factor
    
    def _get_attacked_squares(self, square: chess.Square) -> Set[chess.Square]:
        """Get squares attacked by piece at given square"""
        return self.engine.get_attacked_squares(square)
    
    def _find_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Base implementation for finding tactical opportunities
        
        Subclasses can override to add piece-specific opportunities
        """
        opportunities = []
        
        # Set up position in engine
        self.engine.set_position(position.fen, position.move_history)
        
        # Make the move
        self.engine.make_move(move)
        
        # Get attacked squares after the move
        piece_square = chess.parse_square(move[2:4])
        attacked_squares = self._get_attacked_squares(piece_square)
        
        # Look for forks
        fork_opportunities = self._find_forks(piece_square, attacked_squares)
        opportunities.extend(fork_opportunities)
        
        # Look for discovered attacks
        discovered_opportunities = self._find_discovered_attacks(piece_square, position, move)
        opportunities.extend(discovered_opportunities)
        
        return opportunities

    def _find_forks(self, piece_square: chess.Square, 
                    attacked_squares: Set[chess.Square]) -> List[TacticalOpportunity]:
        """Find fork opportunities where piece attacks multiple valuable pieces.
        
        Args:
            piece_square: Square where our piece is after the move
            attacked_squares: Squares that our piece attacks
            
        Note: This is called AFTER making our move, so engine.get_turn() will be the opponent's color
        """
        opportunities = []
        attacked_pieces = []
        
        # Get the color of our piece (opposite of current turn)
        our_piece = self.engine.get_piece_at(piece_square)
        if not our_piece:
            return []
            
        # Collect enemy pieces being attacked
        for square in attacked_squares:
            piece = self.engine.get_piece_at(square)
            if piece and piece.color != our_piece.color:  # If it's an enemy piece
                attacked_pieces.append((square, piece))
                
        # Look for valuable combinations (2 or more pieces)
        if len(attacked_pieces) >= 2:
            target_squares = {s for s, _ in attacked_pieces}
            target_pieces = [p for _, p in attacked_pieces]
            
            # Calculate fork value based on piece values
            value = sum(self._get_piece_value(p) for p in target_pieces)
            
            # Generate description
            desc = self._generate_fork_description(target_pieces, value)
            
            # Confidence based on protection
            confidence = self._calculate_tactic_confidence(piece_square, target_squares)
            
            opportunities.append(TacticalOpportunity(
                type='fork',
                target_squares=target_squares,
                target_pieces=target_pieces,
                value=value,
                description=desc,
                confidence=confidence
            ))
            
        return opportunities

    def _find_discovered_attacks(self, piece_square: 'chess.Square',
                               position: Position, move: str) -> List[TacticalOpportunity]:
        """Find opportunities where piece move reveals attack from another piece
        
        Args:
            piece_square: Square where the piece will be after the move
            position: Current position before the move
            move: Move in UCI format
            
        Returns:
            List of discovered attack opportunities
        """
        opportunities = []
        
        # Get the original position before the piece moved
        self.engine.set_position(position.fen, position.move_history)
        
        # Find our attacking pieces (excluding the piece that moved)
        our_pieces = {
            square: piece for square, piece in self.engine.get_piece_map().items()
            if piece.color == self.engine.get_turn() and square != piece_square
        }
        # Make the move
        self.engine.make_move(move)
        
        # Get enemy pieces after the move
        enemy_pieces = {}
        piece_map = self.engine.get_piece_map()
        enemy_color = not self.engine.get_turn()
        
        # Iterate through all pieces and collect enemy pieces
        for square, piece in piece_map.items():
            if piece.color != enemy_color:
                enemy_pieces[square] = piece

        # Validate we found enemy pieces
        if not enemy_pieces:
            # No enemy pieces found - this is likely an error state
            # Return empty dict but log warning
            print("Warning: No enemy pieces found in position")
        # Check each of our pieces for potential discovered attacks
        for our_square, our_piece in our_pieces.items():
            # Skip if piece is not a sliding piece (bishop, rook, queen)
            if our_piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                continue
                
            # Get attacked squares for this piece before and after piece move
            self.engine.set_position(position.fen, position.move_history)
            before_squares = self._get_attacked_squares(our_square)
            
            # Get attacked squares after the move
            self.engine.set_position(position.fen, position.move_history)
            self.engine.make_move(move)
            after_squares = self._get_attacked_squares(our_square)
            
            # Find newly attacked squares
            new_squares = after_squares - before_squares
            
            # Check if any enemy pieces are in newly attacked squares
            for enemy_square, enemy_piece in enemy_pieces.items():
                if enemy_square in new_squares:
                    # We found a discovered attack!
                    value = self._get_piece_value(enemy_piece)
                    confidence = self._calculate_tactic_confidence(our_square, {enemy_square})
                    
                    desc = self._generate_discovered_attack_description(
                        our_piece, enemy_piece, value)
                    
                    opportunities.append(TacticalOpportunity(
                        type='discovered_attack',
                        target_squares={enemy_square},
                        target_pieces=[enemy_piece],
                        value=value,
                        description=desc,
                        confidence=confidence
                    ))
        
        return opportunities

    def _get_piece_value(self, piece: chess.Piece) -> float:
        """Get standard piece value with personality-based adjustments"""
        base_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # Kings aren't counted in material
        }
        
        value = base_values[piece.piece_type]
        
        # Adjust based on personality
        if hasattr(self, 'emotional_state') and self.emotional_state.aggression > 0.7:
            # More aggressive pieces value attacking pieces higher
            value *= 1.2
            
        return value

    def _calculate_tactic_confidence(self, piece_square: chess.Square,
                                   target_squares: Set[chess.Square]) -> float:
        """Calculate how confident we are in a tactical opportunity"""
        # Base confidence from emotional state if available
        confidence = getattr(self, 'emotional_state', None).confidence if hasattr(self, 'emotional_state') else 0.5
        
        # Reduce confidence if piece is under attack
        if self.engine.is_attacked_by(not self.engine.get_turn(), piece_square):
            confidence *= 0.7
            
        # Reduce confidence if targets are well protected
        for square in target_squares:
            if self.engine.is_attacked_by(not self.engine.get_turn(), square):
                confidence *= 0.8
                
        return min(1.0, max(0.1, confidence))

    def _generate_fork_description(self, target_pieces: List[chess.Piece], value: float) -> str:
        """Generate natural language description of a fork opportunity"""
        piece_names = [p.symbol().upper() for p in target_pieces]
        
        # More excited language if we're feeling confident (if we have emotional state)
        if hasattr(self, 'emotional_state'):
            if self.emotional_state.confidence > 0.7:
                return f"A brilliant fork targeting {' and '.join(piece_names)}! ({value:0.1f})"
            elif self.emotional_state.confidence < 0.3:
                return f"I see a possible fork against {' and '.join(piece_names)}... though I'm not entirely sure ({value:0.1f})"
        
        return f"A fork opportunity against {' and '.join(piece_names)} ({value:0.1f})"

    def _generate_discovered_attack_description(self, our_piece: chess.Piece, 
                                              enemy_piece: chess.Piece,
                                              value: float) -> str:
        """Generate description for a discovered attack opportunity"""
        our_name = our_piece.symbol().upper()
        enemy_name = enemy_piece.symbol().upper()
        
        if hasattr(self, 'emotional_state'):
            if self.emotional_state.confidence > 0.7:
                return f"By moving away, I'll unleash our {our_name}'s attack on their {enemy_name}! ({value:0.1f})"
            elif self.emotional_state.confidence < 0.3:
                return f"This might create an attack from our {our_name} against their {enemy_name}... ({value:0.1f})"
        
        return f"Moving away reveals our {our_name}'s attack on their {enemy_name} ({value:0.1f})"

    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on personality and analysis
        
        This should be overridden by specific piece agents to provide
        character-appropriate arguments
        """
        raise NotImplementedError(
            "Specific piece agents must implement _generate_argument"
        )