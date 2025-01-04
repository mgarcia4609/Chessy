from dataclasses import dataclass
from typing import Dict, List

from debate_system.protocols import GameMoment, Position, Trigger


@dataclass
class GameMemory:
    """Tracks significant game events and their emotional impact"""
    
    key_moments: List[GameMoment]
    narrative_threads: Dict[str, List[str]]  # Piece -> their story
    emotional_triggers: Dict[str, List[Trigger]]  # What affects each piece
    
    def record_moment(self, position: Position, move: str, 
                     emotional_impact: Dict[str, float]):
        """Record a significant game moment"""
        moment = GameMoment(
            position=position,
            move=move,
            impact=emotional_impact,
            turn=len(self.key_moments) + 1
        )
        self.key_moments.append(moment)
        
        # Update narrative threads
        piece = self.get_moving_piece(move)
        self.narrative_threads[piece].append(
            self.generate_moment_narrative(moment))
        
        # Update emotional triggers
        if abs(max(emotional_impact.values())) > 0.2:
            self.emotional_triggers[piece].append(
                Trigger(position.pattern, emotional_impact))
    
    def generate_argument_context(self, piece: str, 
                                position: Position) -> str:
        """Generate contextual argument based on piece's history"""
        relevant_moments = self.find_relevant_moments(piece, position)
        emotional_state = self.calculate_current_emotion(piece)
        
        return self.generate_narrative(
            piece, relevant_moments, emotional_state)