"""Factory for creating chess piece personalities"""
from typing import Dict
from dataclasses import dataclass

from debate_system.protocols import PersonalityConfig

@dataclass
class PersonalityTemplate:
    """Template for creating piece personalities"""
    name: str
    title: str  # e.g., "Sir", "Bishop", "Queen"
    description_template: str
    options: Dict[str, int]
    tactical_weight: float
    positional_weight: float
    risk_tolerance: float

class PersonalityFactory:
    """Factory for creating chess piece personalities"""
    
    # Default personality templates for each piece type
    DEFAULT_TEMPLATES = {
        'N': PersonalityTemplate(
            name="Galahop",
            title="Sir",
            description_template="A daring knight who loves complex tactical positions",
            options={
                'QS': 100,  # Quick tactical evaluation
                'EVAL_ROUGHNESS': 20  # Willing to take risks
            },
            tactical_weight=1.2,
            positional_weight=0.8,
            risk_tolerance=0.7
        ),
        'B': PersonalityTemplate(
            name="Longview",
            title="Bishop",
            description_template="A strategic bishop who thinks in long diagonals",
            options={
                'QS': 200,  # Deeper evaluation
                'EVAL_ROUGHNESS': 10  # More precise
            },
            tactical_weight=0.9,
            positional_weight=1.3,
            risk_tolerance=0.4
        ),
        'R': PersonalityTemplate(
            name="Steadfast",
            title="Rook",
            description_template="A solid rook who values control and safety",
            options={
                'QS': 150,  # Balanced evaluation
                'EVAL_ROUGHNESS': 15  # Moderate precision
            },
            tactical_weight=1.0,
            positional_weight=1.1,
            risk_tolerance=0.3
        ),
        'Q': PersonalityTemplate(
            name="Dynamica",
            title="Queen",
            description_template="An aggressive queen who seeks initiative",
            options={
                'QS': 80,  # Quick to act
                'EVAL_ROUGHNESS': 25  # Embraces chaos
            },
            tactical_weight=1.3,
            positional_weight=0.7,
            risk_tolerance=0.8
        ),
        'K': PersonalityTemplate(
            name="Prudence",
            title="King",
            description_template="A cautious king who prioritizes safety",
            options={
                'QS': 250,  # Very thorough evaluation
                'EVAL_ROUGHNESS': 5  # Very precise
            },
            tactical_weight=0.8,
            positional_weight=1.2,
            risk_tolerance=0.2
        ),
        'P': PersonalityTemplate(
            name="Pioneer",
            title="Pawn",
            description_template="An ambitious pawn who dreams of promotion",
            options={
                'QS': 120,  # Moderate evaluation
                'EVAL_ROUGHNESS': 18  # Willing to gambit
            },
            tactical_weight=1.1,
            positional_weight=1.0,
            risk_tolerance=0.6
        )
    }
    
    def __init__(self, templates: Dict[str, PersonalityTemplate] = None):
        """Initialize the factory with personality templates
        
        Args:
            templates: Optional custom templates. If None, uses defaults.
        """
        self.templates = templates or self.DEFAULT_TEMPLATES.copy()
    
    def create_personality(self, piece_type: str, index: int = 0) -> PersonalityConfig:
        """Create a personality for a piece
        
        Args:
            piece_type: The type of piece ('P', 'N', 'B', 'R', 'Q', 'K')
            index: Optional index for creating multiple personalities of same type
            
        Returns:
            PersonalityConfig for the piece
        """
        if piece_type not in self.templates:
            raise ValueError(f"No personality template for piece type: {piece_type}")
            
        template = self.templates[piece_type]
        
        # Add index to name if needed
        name_suffix = f" {index+1}" if index > 0 else ""
        full_name = f"{template.title} {template.name}{name_suffix}"
        
        return PersonalityConfig(
            name=full_name,
            description=template.description_template,
            options=template.options.copy(),
            tactical_weight=template.tactical_weight,
            positional_weight=template.positional_weight,
            risk_tolerance=template.risk_tolerance
        )
    
    def create_all_personalities(self) -> Dict[str, PersonalityConfig]:
        """Create personalities for all piece types
        
        Returns:
            Dict mapping piece types to their personalities
        """
        return {
            piece_type: self.create_personality(piece_type)
            for piece_type in self.templates
        }
    
    def create_themed_personality(self, piece_type: str, theme: str) -> PersonalityConfig:
        """Create a themed variation of a piece's personality
        
        Args:
            piece_type: The type of piece
            theme: The theme to apply (e.g., 'aggressive', 'defensive', 'creative')
            
        Returns:
            A modified PersonalityConfig based on the theme
        """
        base = self.create_personality(piece_type)
        
        if theme == 'aggressive':
            base.tactical_weight *= 1.2
            base.risk_tolerance = min(1.0, base.risk_tolerance * 1.3)
            base.options['EVAL_ROUGHNESS'] = min(30, base.options['EVAL_ROUGHNESS'] * 1.5)
            base.description = f"An aggressive variant of {base.description}"
            
        elif theme == 'defensive':
            base.positional_weight *= 1.2
            base.risk_tolerance = max(0.1, base.risk_tolerance * 0.7)
            base.options['QS'] = min(300, base.options['QS'] * 1.5)
            base.description = f"A defensive variant of {base.description}"
            
        elif theme == 'creative':
            base.tactical_weight *= 1.1
            base.positional_weight *= 1.1
            base.options['EVAL_ROUGHNESS'] = min(30, base.options['EVAL_ROUGHNESS'] * 1.3)
            base.description = f"A creative variant of {base.description}"
            
        return base 