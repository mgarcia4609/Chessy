from dataclasses import dataclass
from typing import Dict, List, Tuple

from debate_system.protocols import Interaction


@dataclass
class RelationshipNetwork:
    """Tracks relationships between pieces"""
    trust_matrix: Dict[Tuple[str, str], float]  # (piece1, piece2) -> trust level
    recent_interactions: List[Interaction]  # Last N interactions
    
    def get_support_bonus(self, piece1: str, piece2: str) -> float:
        """Calculate bonus for pieces working together"""
        trust = self.trust_matrix.get((piece1, piece2), 0.5)
        recent = self.get_recent_cooperation(piece1, piece2)
        return trust * (1 + recent * 0.5)  # Recent cooperation amplifies trust