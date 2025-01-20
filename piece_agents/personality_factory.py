from typing import Dict, Optional, TYPE_CHECKING
from .personality_defaults import DEFAULT_TEMPLATES, INTERACTION_PROFILES
from debate_system.protocols import InteractionProfile, PersonalityConfig, PersonalityTemplate, PersonalityTrait

if TYPE_CHECKING:
    from debate_system.protocols import InteractionProfile, PersonalityConfig, PersonalityTemplate, PersonalityTrait

class PersonalityFactory:
    """Factory for creating chess piece personalities with rich interaction potential"""

    def __init__(self, templates: Optional[Dict[str, 'PersonalityTemplate']] = None, interaction_profiles: Optional[Dict[str, 'InteractionProfile']] = None):
        """Initialize the factory with personality templates"""
        self.templates = templates or DEFAULT_TEMPLATES.copy()
        self.interaction_profiles = interaction_profiles or INTERACTION_PROFILES.copy()

    def create_personality(self, piece_type: str, index: int = 0) -> 'PersonalityConfig':
        """Create a personality for a piece with rich interaction potential"""
        if piece_type not in self.templates:
            raise ValueError(f"No personality template for piece type: {piece_type}")

        template = self.templates[piece_type]
        profile = self.interaction_profiles[piece_type]

        # Add index to name if needed
        name_suffix = f" {index+1}" if index > 0 else ""
        full_name = f"{template.title} {template.name}{name_suffix}"
        
        # Enhance description with interaction style
        full_description = (
            f"{template.description_template}. "
            f"{profile.cooperation_style}. "
            f"{profile.conflict_style}."
        )
        
        return PersonalityConfig(
            name=full_name,
            description=full_description,
            options=template.options.copy(),
            tactical_weight=template.tactical_weight,
            positional_weight=template.positional_weight,
            risk_tolerance=template.risk_tolerance
        )
    
    def create_all_personalities(self) -> Dict[str, 'PersonalityConfig']:
        """Create personalities for all piece types"""
        return {
            piece_type: self.create_personality(piece_type)
            for piece_type in self.templates
        }
    
    def create_themed_personality(self, piece_type: str, theme: str) -> 'PersonalityConfig':
        """Create a themed variation of a piece's personality that maintains their core traits"""
        base = self.create_personality(piece_type)
        profile = self.interaction_profiles[piece_type]
        
        if theme == 'aggressive':
            # Maintain character while being more aggressive
            base.tactical_weight *= 1.2
            base.risk_tolerance = min(1.0, base.risk_tolerance * 1.3)
            base.options['EVAL_ROUGHNESS'] = min(30, base.options['EVAL_ROUGHNESS'] * 1.5)
            
            # Adjust description based on piece's primary traits
            if PersonalityTrait.DRAMATIC in profile.primary_traits:
                base.description = f"An aggressively dramatic variant who {profile.conflict_style.lower()}"
            elif PersonalityTrait.ZEALOUS in profile.primary_traits:
                base.description = f"A zealously aggressive variant who {profile.conflict_style.lower()}"
            else:
                base.description = f"An aggressive variant who {profile.conflict_style.lower()}"
            
        elif theme == 'defensive':
            # Maintain character while being more defensive
            base.positional_weight *= 1.2
            base.risk_tolerance = max(0.1, base.risk_tolerance * 0.7)
            base.options['QS'] = min(300, base.options['QS'] * 1.5)
            
            if PersonalityTrait.PROTECTIVE in profile.primary_traits:
                base.description = f"An ultra-defensive variant who {profile.cooperation_style.lower()}"
            elif PersonalityTrait.NEUROTIC in profile.primary_traits:
                base.description = f"An anxiously defensive variant who {profile.cooperation_style.lower()}"
            else:
                base.description = f"A defensive variant who {profile.cooperation_style.lower()}"
            
        elif theme == 'creative':
            # Maintain character while being more creative
            base.tactical_weight *= 1.1
            base.positional_weight *= 1.1
            base.options['EVAL_ROUGHNESS'] = min(30, base.options['EVAL_ROUGHNESS'] * 1.3)
            
            if PersonalityTrait.ADVENTUROUS in profile.primary_traits:
                base.description = f"A wildly creative variant who {profile.leadership_style.lower()}"
            elif PersonalityTrait.THEATRICAL in profile.primary_traits:
                base.description = f"A dramatically creative variant who {profile.leadership_style.lower()}"
            else:
                base.description = f"A creative variant who {profile.leadership_style.lower()}"
            
        return base 