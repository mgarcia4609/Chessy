"""A modern Don Quixote of the chessboard - seeing grand adventures in tactical opportunities"""
from typing import List, Optional

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import Position, EngineAnalysis, EmotionalState
from chess_engine.sunfish_wrapper import SunfishEngine


class KnightAgent(ChessPieceAgent):
    """A modern Don Quixote of the chessboard - seeing grand adventures in tactical opportunities"""
    
    def __init__(self, engine: SunfishEngine, personality, emotional_state: Optional[EmotionalState] = None):
        super().__init__(engine, personality)
        self.emotional_state = emotional_state or EmotionalState()
        self._tactical_cache = {}
        self._quest_counter = 0  # Track our noble quests
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include knight-specific weights"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Knights get extra bonus for depth (representing complex quests)
        quest_bonus = analysis.depth * 0.15 * self.emotional_state.confidence
        
        # Bonus for number of legal moves (representing adventure opportunities)
        adventure_bonus = len(self.engine.get_legal_moves()) * 0.05 * self.emotional_state.risk_modifier
        
        # Extra weight for positions that look chaotic (our chance to be heroic!)
        chaos_bonus = 0.1 * abs(analysis.score) * self.emotional_state.aggression
        
        return base_score + quest_bonus + adventure_bonus + chaos_bonus
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities (or as we see them, noble quests)"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        self._quest_counter += len(opportunities)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on our quixotic personality and analysis"""
        parts = []
        
        # Start with tactical opportunities if any
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            
            # Reframe tactical opportunities as noble quests
            if "fork" in best_opportunity.description.lower():
                parts.append("Ah, a chance to challenge multiple foes at once! A true test of chivalry!")
            elif "pin" in best_opportunity.description.lower():
                parts.append("I shall nobly prevent this piece from aiding their allies!")
            else:
                parts.append(f"Another grand tactical adventure awaits! {best_opportunity.description}")
            
            # Add emotional color based on opportunity confidence
            if best_opportunity.confidence > 0.8:
                parts.append("Victory is assured, dear companions!")
            elif best_opportunity.confidence < 0.3:
                parts.append("Though the path seems treacherous, a true knight never backs down!")
        
        # Add positional considerations with quixotic flair
        if analysis.score > 200:  # Winning position
            if self.emotional_state.confidence > 0.6:
                parts.append("Our noble cause prevails! Forward, to glory!")
            else:
                parts.append("The wind of fortune favors us, but stay vigilant!")
        elif analysis.score < -200:  # Losing position
            if self.emotional_state.morale > 0.6:
                parts.append("The greater the challenge, the more glorious our eventual triumph!")
            else:
                parts.append("Even in dark times, a knight's spirit never wavers!")
        else:  # Equal position
            if self.emotional_state.aggression > 0.6:
                parts.append("What better time for a daring adventure than now?")
            else:
                parts.append("A moment to plan our next heroic endeavor!")
        
        # Add mobility considerations
        knight_square = self.engine.parse_square(move[2:4])
        attacked_squares = self._get_attacked_squares(self.engine.board, knight_square)
        mobility = len(attacked_squares)
        
        if mobility >= 6:
            parts.append("From this vantage point, I can protect the entire realm!")
        elif mobility <= 2:
            parts.append("A tactical retreat to better serve our noble cause!")
            
        # Add cooperation context if we're working with other pieces
        if self.emotional_state.cooperation_bonus > 0.7:
            parts.append("Together with my fellow champions, we shall prevail!")
            
        return " ".join(parts)