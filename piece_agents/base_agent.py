from dataclasses import dataclass
from typing import List, Optional, Dict

from chess_engine.sunfish_wrapper import SunfishEngine
from debate_system.protocols import Position, MoveProposal, EngineAnalysis, PersonalityConfig

@dataclass
class ChessPieceAgent:
    """Base class for chess piece agents"""
    engine: SunfishEngine
    personality: PersonalityConfig
    
    def __post_init__(self):
        """Initialize the engine with personality settings"""
        for option, value in self.personality.options.items():
            self.engine.set_option(option, value)
    
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
        
        # Analyze the position after the move
        best_move, analyses = self.engine.go(movetime=think_time)
        
        # Get the final/deepest analysis
        final_analysis = analyses[-1] if analyses else None
        
        if not final_analysis:
            return None
            
        # Calculate weighted score based on personality
        weighted_score = self._calculate_weighted_score(final_analysis)
        
        # Generate argument based on personality and analysis
        argument = self._generate_argument(position, move, final_analysis)
        
        return MoveProposal(
            move=move,
            score=weighted_score,
            analysis=final_analysis,
            argument=argument
        )
    
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Calculate weighted score based on personality
        
        This is where different piece personalities can emphasize different aspects
        of the position (tactical vs positional, risk vs safety, etc)
        """
        base_score = analysis.score
        
        # Apply personality weights
        tactical_component = base_score * self.personality.tactical_weight
        positional_bonus = (analysis.depth * 10) * self.personality.positional_weight
        
        # Risk adjustment based on personality
        risk_factor = 1.0
        if base_score > 0:
            # Winning positions - aggressive personalities push harder
            risk_factor += (self.personality.risk_tolerance - 0.5) * 0.5
        else:
            # Losing positions - cautious personalities defend harder
            risk_factor += (0.5 - self.personality.risk_tolerance) * 0.5
            
        return (tactical_component + positional_bonus) * risk_factor
    
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on personality and analysis
        
        This should be overridden by specific piece agents to provide
        character-appropriate arguments
        """
        raise NotImplementedError(
            "Specific piece agents must implement _generate_argument"
        ) 