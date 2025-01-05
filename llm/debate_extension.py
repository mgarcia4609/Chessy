from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from debate_system.protocols import DebateRound, GameMemory, PsychologicalState
    from piece_agents.base_agent import ChessPieceAgent


class DebateExtension:
    """Extends debate system with LLM capabilities"""
    def enrich_argument(self, 
                       base_argument: str,
                       game_memory: 'GameMemory',
                       psychological_state: 'PsychologicalState') -> str:
        """Enhance basic arguments with character-driven narrative"""
        
    def generate_debate_dynamics(self,
                               participants: List['ChessPieceAgent'],
                               debate_history: List['DebateRound']) -> Dict[str, str]:
        """Generate inter-character dynamics during debate"""