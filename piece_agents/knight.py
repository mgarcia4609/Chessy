from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from .base_agent import ChessPieceAgent, PersonalityTrait, TraitEffect
from sunfish import Position, Move, PIECE_VALUES

@dataclass
class TacticalOpportunity:
    """Represents a tactical opportunity like a fork or discovered attack"""
    type: str  # 'fork', 'discovered_attack', etc.
    target_squares: Set[int]
    target_pieces: List[str]
    value: float

class KnightAgent(ChessPieceAgent):
    """A knight that loves to create chaos and find tactical opportunities"""
    
    def __init__(self, name: str = None):
        traits = [
            PersonalityTrait(
                name="tactical",
                strength=0.8,
                description="Loves finding forks and other tactical opportunities",
                effects=[TraitEffect.MOVE_SCORE, TraitEffect.ARGUMENT]
            ),
            PersonalityTrait(
                name="unpredictable",
                strength=0.7,
                description="Prefers unusual moves that are harder to anticipate",
                effects=[TraitEffect.MOVE_SCORE, TraitEffect.ARGUMENT]
            ),
            PersonalityTrait(
                name="aggressive",
                strength=0.6,
                description="Likes to push forward and attack",
                effects=[TraitEffect.PIECE_VALUE, TraitEffect.SQUARE_TABLE, TraitEffect.MOVE_SCORE]
            )
        ]
        super().__init__("N", traits, name)
        
        # Cache for tactical analysis
        self._tactical_cache: Dict[Tuple[str, int], List[TacticalOpportunity]] = {}
    
    def _get_knight_moves(self, square: int) -> Set[int]:
        """Get all possible knight move destinations from a square"""
        moves = {
            square - 21, square - 19,
            square - 12, square - 8,
            square + 8, square + 12,
            square + 19, square + 21
        }
        return {s for s in moves if 21 <= s <= 98}
    
    def _analyze_tactical_opportunities(
        self,
        position: Position,
        move: Move
    ) -> List[TacticalOpportunity]:
        """Analyze tactical opportunities from a position"""
        # Check cache first
        cache_key = (position.board, move.j)
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
        
        opportunities = []
        attacked_squares = self._get_knight_moves(move.j)
        
        # Look for forks
        valuable_targets = [
            (square, position.board[square].upper())
            for square in attacked_squares
            if position.board[square].islower()
        ]
        
        if len(valuable_targets) >= 2:
            target_squares = {square for square, _ in valuable_targets}
            target_pieces = [piece for _, piece in valuable_targets]
            
            # Calculate fork value based on targeted pieces
            fork_value = sum(
                PIECE_VALUES[piece] for piece in target_pieces
            )
            
            opportunities.append(TacticalOpportunity(
                type='fork',
                target_squares=target_squares,
                target_pieces=target_pieces,
                value=fork_value
            ))
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
    
    def _apply_trait_modifiers(self, position: Position, move: Move, score: float) -> float:
        """Apply knight-specific trait modifiers"""
        score = super()._apply_trait_modifiers(position, move, score)
        
        # Check for tactical opportunities
        if "tactical" in self.traits:
            opportunities = self._analyze_tactical_opportunities(position, move)
            for opp in opportunities:
                score += opp.value * self.traits["tactical"].strength
        
        # Unpredictable knights prefer unusual squares
        if "unpredictable" in self.traits:
            # Central squares are more "predictable"
            central_squares = {44, 45, 54, 55}
            if move.j not in central_squares:
                score *= (1 + 0.1 * self.traits["unpredictable"].strength)
            
            # Bonus for moves that are harder to defend against
            attacked_squares = self._get_knight_moves(move.j)
            defender_count = sum(
                1 for s in attacked_squares
                if position.board[s].isupper()  # Friendly piece
            )
            if defender_count == 0:  # Harder to defend against
                score *= (1 + 0.05 * self.traits["unpredictable"].strength)
        
        return score
    
    def generate_argument(self, position: Position, move: Move, score: float) -> str:
        """Generate a knight-specific argument for the move"""
        # Start with basic argument
        argument_parts = []
        base_argument = super().generate_argument(position, move, score)
        argument_parts.append(base_argument)
        
        # Add tactical considerations
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            for opp in opportunities:
                if opp.type == 'fork':
                    pieces = ' and '.join(opp.target_pieces)
                    argument_parts.append(f"From there I can fork their {pieces}!")
        
        # Add personality flair
        if "unpredictable" in self.traits and self.traits["unpredictable"].strength > 0.5:
            attacked_squares = self._get_knight_moves(move.j)
            defender_count = sum(
                1 for s in attacked_squares
                if position.board[s].isupper()
            )
            if defender_count == 0:
                argument_parts.append(
                    "They'll have a hard time defending against this unusual maneuver!"
                )
        
        return " ".join(argument_parts) 