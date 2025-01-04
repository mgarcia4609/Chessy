"""A knight that loves to create chaos and find tactical opportunities"""
from typing import List, Optional
import chess

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import Position, EngineAnalysis, EmotionalState
from chess_engine.sunfish_wrapper import SunfishEngine


class KnightAgent(ChessPieceAgent):
    """A knight that loves to create chaos and find tactical opportunities"""
    
    def __init__(self, engine: SunfishEngine, personality, emotional_state: Optional[EmotionalState] = None):
        super().__init__(engine, personality)
        self.emotional_state = emotional_state or EmotionalState()
        self._tactical_cache = {}
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include knight-specific weights"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Knights get extra bonus for depth (representing complex tactics)
        depth_bonus = analysis.depth * 0.1 * self.emotional_state.confidence
        
        # Bonus for number of legal moves (knight mobility)
        mobility_bonus = len(analysis.legal_moves) * 0.05 * self.emotional_state.risk_modifier
        
        return base_score + depth_bonus + mobility_bonus
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on personality and analysis"""
        parts = []
        
        # Start with tactical opportunities if any
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
            
            # Add emotional color based on opportunity confidence
            if best_opportunity.confidence > 0.8:
                parts.append("I'm very confident about this tactical shot!")
            elif best_opportunity.confidence < 0.3:
                parts.append("Though we should be careful about potential defenses...")
        
        # Add positional considerations
        if analysis.score > 200:  # Winning position
            if self.emotional_state.confidence > 0.6:
                parts.append("This position is clearly winning for us!")
            else:
                parts.append("I believe we're winning, but let's stay focused.")
        elif analysis.score < -200:  # Losing position
            if self.emotional_state.morale > 0.6:
                parts.append("We're in a tough spot, but this move gives us fighting chances!")
            else:
                parts.append("Things look grim, but we must keep trying.")
        else:  # Equal position
            if self.emotional_state.aggression > 0.6:
                parts.append("The position is balanced, but this move creates chaos and opportunities!")
            else:
                parts.append("A solid move that maintains the balance while looking for chances.")
        
        # Add mobility considerations
        knight_square = chess.parse_square(move[2:4])
        attacked_squares = self._get_attacked_squares(chess.Board(position.fen), knight_square)
        mobility = len(attacked_squares)
        
        if mobility >= 6:
            parts.append("I'll have excellent mobility after this move!")
        elif mobility <= 2:
            parts.append("My mobility will be limited, but sometimes we need to make sacrifices.")
            
        # Add cooperation context if we're working with other pieces
        if self.emotional_state.cooperation_bonus > 0.7:
            parts.append("This coordinates well with our other pieces.")
            
        return " ".join(parts)