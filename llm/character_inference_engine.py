from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from debate_system.protocols import GameMemory, GameMoment, LLMContext, PersonalityConfig, PsychologicalState


class CharacterInferenceEngine:
    """Manages LLM-based character development"""
    def generate_response(self, context: 'LLMContext') -> str:
        """Generate character-appropriate response"""
        
    def evolve_personality(self, 
                          memory: 'GameMemory',
                          psychological_state: 'PsychologicalState') -> 'PersonalityConfig':
        """Evolve personality based on experiences"""
        
    def interpret_game_moment(self, moment: 'GameMoment') -> List[str]:
        """Generate narrative interpretations of game events"""