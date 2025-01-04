from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

@dataclass
class EngineAnalysis:
    """Analysis results from the engine"""
    depth: int
    score: int
    pv: List[str]  # Principal variation (planned moves)
    nodes: int
    time_ms: int
    nps: int  # Nodes per second

@dataclass
class Position:
    """Chess position representation"""
    fen: str
    move_history: List[str]  # UCI format moves
    
    @property
    def is_white_to_move(self) -> bool:
        """Determine if white to move based on FEN"""
        return self.fen.split()[1] == 'w'

@dataclass
class MoveProposal:
    """A proposed move from a piece"""
    move: str  # UCI format (e.g. 'e2e4')
    score: float
    analysis: EngineAnalysis
    argument: str

@dataclass
class DebateRound:
    """Records a round of debate"""
    position: Position
    proposals: List[MoveProposal]
    winning_proposal: Optional[MoveProposal] = None

# Engine personality configuration
@dataclass
class PersonalityConfig:
    """Configuration for engine personality"""
    name: str
    description: str
    options: Dict[str, int]  # Engine option name -> value
    
    # Personality-specific evaluation weights
    tactical_weight: float = 1.0  # Weight for tactical evaluation
    positional_weight: float = 1.0  # Weight for positional factors
    risk_tolerance: float = 0.5  # 0 = very cautious, 1 = very aggressive
