"""A contemplative bishop who sees the board as a spiritual battlefield"""
from typing import List, Optional
import chess

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import PersonalityConfig, Position, EngineAnalysis, EmotionalState
from chess_engine.sunfish_wrapper import ChessEngine


class BishopAgent(ChessPieceAgent):
    """A bishop who views chess as a metaphysical battle between light and dark squares"""
    
    def __init__(self, engine: ChessEngine, personality: PersonalityConfig, emotional_state: Optional[EmotionalState] = None, board_piece: Optional[chess.Piece] = None, square: Optional[chess.Square] = None):
        super().__init__(engine, personality, emotional_state, board_piece, square)
        # Track spiritual state
        self.current_square_color = None    # Light or dark squares bishop
        self.fellow_bishop_present = False  # Whether our fellow missionary is still with us
        self.potential_converts = set()     # Squares where enemy pieces might be "receptive"
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include bishop-specific spiritual weights"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Bishops value their spiritual mission over pure tactics
        spiritual_bonus = 0.0
        
        # Bonus for maintaining "clean" diagonal paths (paths of enlightenment)
        if self._has_clear_diagonals():
            spiritual_bonus += 0.3 * self.emotional_state.confidence
            
        # Extra value when working with fellow bishop (joint ministry)
        if self.fellow_bishop_present:
            spiritual_bonus += 0.2 * self.emotional_state.cooperation_bonus
            
        # Bonus for positions that allow "preaching" to multiple pieces
        preaching_positions = self._count_preaching_opportunities()
        if preaching_positions > 2:
            spiritual_bonus += 0.15 * preaching_positions * self.emotional_state.morale
            
        # Risk tolerance increases with religious fervor
        risk_factor = 1.0 + (self.emotional_state.confidence * 0.3)
        
        return (base_score + spiritual_bonus) * risk_factor
        
    def _has_clear_diagonals(self) -> bool:
        """Check if bishop has clear diagonal paths (paths of enlightenment)"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == chess.BISHOP and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return False
            
        # Count unobstructed diagonal squares
        attacked = self.engine.get_attacked_squares(piece_square)
        return len(attacked) >= 7  # Good diagonal coverage
        
    def _count_preaching_opportunities(self) -> int:
        """Count how many enemy pieces we can potentially 'convert'"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == chess.BISHOP and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return 0
            
        # Count enemy pieces we can reach
        attacked = self.engine.get_attacked_squares(piece_square)
        enemy_pieces = sum(1 for square in attacked 
                         if self.engine.get_piece_at(square) and 
                         self.engine.get_piece_at(square).color != self.engine.get_turn())
        return enemy_pieces
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities through a spiritual lens"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        
        # Add spiritual context to opportunities
        for opp in opportunities:
            if opp.type == 'fork':
                opp.description = self._add_spiritual_context_to_fork(opp)
            elif opp.type == 'discovered_attack':
                opp.description = self._add_spiritual_context_to_discovery(opp)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _add_spiritual_context_to_fork(self, opp: TacticalOpportunity) -> str:
        """Add spiritual context to fork descriptions"""
        base_desc = opp.description
        
        if self.emotional_state.confidence > 0.7:
            return f"The light guides us to spread our message to multiple lost souls! {base_desc}"
        elif self.emotional_state.confidence < 0.3:
            return f"Perhaps through gentle guidance we can show them the way... {base_desc}"
        else:
            return f"An opportunity to minister to multiple pieces. {base_desc}"
            
    def _add_spiritual_context_to_discovery(self, opp: TacticalOpportunity) -> str:
        """Add spiritual context to discovered attack descriptions"""
        base_desc = opp.description
        
        if self.emotional_state.confidence > 0.7:
            return f"By moving aside, we create a divine path for our allies! {base_desc}"
        elif self.emotional_state.confidence < 0.3:
            return f"The ways of providence are mysterious... {base_desc}"
        else:
            return f"Our movement reveals new paths of enlightenment. {base_desc}"
            
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on spiritual considerations"""
        parts = []
        
        # Start with tactical/spiritual opportunities
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
        
        # Add positional considerations with spiritual context
        if analysis.score > 200:  # Winning position
            if self.emotional_state.confidence > 0.7:
                parts.append("The light of truth shines brightly on our position!")
            else:
                parts.append("We must remain humble in our advantage.")
        elif analysis.score < -200:  # Losing position
            if self.emotional_state.morale > 0.6:
                parts.append("Though we face trials, our faith remains unshaken!")
            else:
                parts.append("Even in darkness, we must keep our faith...")
        else:  # Equal position
            if self.emotional_state.aggression > 0.6:
                parts.append("Let us spread our message with renewed vigor!")
            else:
                parts.append("We maintain our vigil, ready to guide any who seek truth.")
        
        # Add diagonal path considerations
        if self._has_clear_diagonals():
            parts.append("This position grants us clear paths to spread our message!")
        
        # Add cooperation context
        if self.fellow_bishop_present and self.emotional_state.cooperation_bonus > 0.7:
            parts.append("Together with our fellow missionary, we shall illuminate the way!")
            
        # Add preaching opportunity context
        preaching_ops = self._count_preaching_opportunities()
        if preaching_ops > 2:
            parts.append(f"From here we can minister to {preaching_ops} souls!")
            
        return " ".join(parts) 