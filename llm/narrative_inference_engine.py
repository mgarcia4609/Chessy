from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from debate_system.protocols import DebateRound, GameMemory, PsychologicalState
    from piece_agents.base_agent import ChessPieceAgent


class NarrativeInferenceEngine:
    """LLM-driven narrative generation"""
    def interpret_game_history(self, 
                             memory: 'GameMemory',
                             piece: 'ChessPieceAgent') -> List[str]:
        """Generate character-specific interpretations"""
        
    def create_character_arc(self,
                           psychological_state: 'PsychologicalState',
                           debate_history: List['DebateRound']) -> str:
        """Develop character arc based on game events"""