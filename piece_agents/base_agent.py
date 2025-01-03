from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, ClassVar
from enum import Enum
import copy
from sunfish import Position, Move, piece as PIECE_VALUES, pst as PIECE_SQUARE_TABLES

class TraitEffect(Enum):
    """Types of effects a trait can have"""
    PIECE_VALUE = "piece_value"
    SQUARE_TABLE = "square_table"
    MOVE_SCORE = "move_score"
    ARGUMENT = "argument"

@dataclass
class PersonalityTrait:
    """Represents a personality trait and its strength"""
    name: str
    strength: float  # 0.0 to 1.0
    description: str
    effects: List[TraitEffect]

class ChessPieceAgent:
    """Base class for chess piece agents with personality-driven behavior"""
    
    # Class-level trait definitions that can be used by all pieces
    TRAITS: ClassVar[Dict[str, PersonalityTrait]] = {
        "aggressive": PersonalityTrait(
            name="aggressive",
            strength=0.7,
            description="Prefers attacking moves and forward positions",
            effects=[TraitEffect.PIECE_VALUE, TraitEffect.SQUARE_TABLE, TraitEffect.MOVE_SCORE]
        ),
        "cautious": PersonalityTrait(
            name="cautious",
            strength=0.6,
            description="Prefers safe moves and defensive positions",
            effects=[TraitEffect.PIECE_VALUE, TraitEffect.SQUARE_TABLE, TraitEffect.MOVE_SCORE]
        ),
        "protective": PersonalityTrait(
            name="protective",
            strength=0.5,
            description="Values staying near friendly pieces",
            effects=[TraitEffect.MOVE_SCORE, TraitEffect.ARGUMENT]
        )
    }
    
    def __init__(self, piece_type: str, traits: List[PersonalityTrait], name: str = None):
        """
        Initialize a chess piece agent
        
        Args:
            piece_type: One of 'P', 'N', 'B', 'R', 'Q', 'K'
            traits: List of personality traits that influence behavior
            name: Optional name for the piece (e.g. "Kingside Knight")
        """
        if piece_type not in PIECE_VALUES:
            raise ValueError(f"Invalid piece type: {piece_type}")
        
        self.piece_type = piece_type
        self.traits = {trait.name: trait for trait in traits}
        self.name = name or f"{piece_type}"
        
        # Store original values for reference
        self._original_piece_value = PIECE_VALUES[self.piece_type]
        self._original_square_table = copy.deepcopy(PIECE_SQUARE_TABLES[self.piece_type])
        
        # Create our own copies of the evaluation tables
        self.piece_value = self._modify_piece_value()
        self.square_table = self._modify_square_table()
    
    def _modify_piece_value(self) -> int:
        """Modify base piece value based on personality traits"""
        value = self._original_piece_value
        
        for trait in self.traits.values():
            if TraitEffect.PIECE_VALUE not in trait.effects:
                continue
                
            if trait.name == "aggressive":
                value *= (1 + 0.2 * trait.strength)
            elif trait.name == "cautious":
                value *= (1 - 0.1 * trait.strength)
        
        return int(value)
    
    def _modify_square_table(self) -> Tuple[int, ...]:
        """Modify piece-square table based on personality"""
        table = list(self._original_square_table)
        
        for trait in self.traits.values():
            if TraitEffect.SQUARE_TABLE not in trait.effects:
                continue
                
            if trait.name == "aggressive":
                # Prefer forward positions
                table = [
                    v * (1 + 0.1 * trait.strength) if 60 <= i <= 90 else v 
                    for i, v in enumerate(table)
                ]
            elif trait.name == "cautious":
                # Prefer back ranks
                table = [
                    v * (1 + 0.1 * trait.strength) if i >= 90 else v 
                    for i, v in enumerate(table)
                ]
        
        return tuple(table)
    
    def evaluate_move(self, position: Position, move: Move) -> float:
        """
        Evaluate a potential move considering personality traits
        
        Args:
            position: Current board position
            move: Potential move to evaluate
            
        Returns:
            float: Score for the move, higher is better
        """
        score = self._calculate_base_score(position, move)
        score = self._apply_trait_modifiers(position, move, score)
        return score
    
    def _calculate_base_score(self, position: Position, move: Move) -> float:
        """Calculate base score using our modified evaluation tables"""
        i, j = move.i, move.j
        score = self.square_table[j] - self.square_table[i]
        
        # Add capture value if applicable
        captured = position.board[j]
        if captured.islower():
            score += PIECE_VALUES[captured.upper()]
        
        return float(score)
    
    def _apply_trait_modifiers(self, position: Position, move: Move, score: float) -> float:
        """Apply personality trait modifiers to move score"""
        for trait in self.traits.values():
            if TraitEffect.MOVE_SCORE not in trait.effects:
                continue
                
            if trait.name == "aggressive":
                # Bonus for captures and forward movement
                if position.board[move.j].islower():
                    score *= (1 + 0.3 * trait.strength)
                if move.j < move.i:  # Moving forward
                    score *= (1 + 0.1 * trait.strength)
                    
            elif trait.name == "protective":
                # Bonus for moves near friendly pieces
                friendly_count = sum(1 for p in position.board[move.j-10:move.j+10] 
                                  if p.isupper())
                score += friendly_count * 10 * trait.strength
        
        return score
    
    def generate_argument(self, position: Position, move: Move, score: float) -> str:
        """
        Generate a natural language argument for why this move should be chosen
        
        Args:
            position: Current board position
            move: The move being argued for
            score: The calculated score for the move
            
        Returns:
            str: A natural language argument for the move
        """
        argument_parts = []
        
        # Basic move description
        captured = position.board[move.j]
        argument_parts.append(
            f"I propose moving to {chr(ord('a') + move.j%10)}{move.j//10}"
        )
        
        if captured.islower():
            argument_parts.append(f"capturing their {captured.upper()}")
        
        # Add personality-flavored justification
        for trait in self.traits.values():
            if TraitEffect.ARGUMENT not in trait.effects:
                continue
                
            if trait.name == "aggressive" and trait.strength > 0.5:
                argument_parts.append("which gives us a strong attacking position!")
            elif trait.name == "protective" and trait.strength > 0.5:
                argument_parts.append("where I can better protect our pieces.")
        
        return " ".join(argument_parts) 