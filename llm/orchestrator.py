from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from debate_system.moderator import DebateModerator
    from debate_system.protocols import GameMemory, GameMoment, PsychologicalState


class Orchestrator:
    """Coordinates LLM interactions with game systems"""
    
    def __init__(self, debate_moderator: 'DebateModerator', 
                 game_memory: 'GameMemory',
                 psychological_state: 'PsychologicalState'):
        self.debate_moderator = debate_moderator
        self.game_memory = game_memory
        self.psychological_state = psychological_state
        
    async def process_game_moment(self, moment: 'GameMoment'):
        """Process game events through LLM for rich narrative"""
        # Update psychological state
        impact = self.psychological_state.simulate_psychological_impact(moment.move)
        
        # Generate narrative interpretation
        narrative = await self.generate_narrative_interpretation(
            moment, impact, self.game_memory
        )
        
        # Update character relationships
        await self.update_relationships(moment, narrative)
        
        # Evolve character personalities
        await self.evolve_characters(self.game_memory, self.psychological_state)