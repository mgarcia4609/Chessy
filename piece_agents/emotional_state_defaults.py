"""Default emotional states for chess pieces"""
from typing import Dict
from debate_system.protocols import EmotionalState

# Default emotional states for each piece type
DEFAULT_EMOTIONAL_STATES: Dict[str, EmotionalState] = {
    'N': EmotionalState(
        confidence=0.7,    # Quixotic bravery
        morale=0.8,       # Enthusiastic about adventures
        trust=0.6,        # Trusting but not naive
        aggression=0.7    # Ready for "noble quests"
    ),
    'B': EmotionalState(
        confidence=0.6,    # Confident in their mission
        morale=0.7,       # Spiritually motivated
        trust=0.4,        # Suspicious of non-believers
        aggression=0.5    # Zealous but measured
    ),
    'R': EmotionalState(
        confidence=0.3,    # Anxious about leaving safety
        morale=0.5,       # Stable but nervous
        trust=0.7,        # Values defensive alliances
        aggression=0.2    # Prefers fortification to attack
    ),
    'Q': EmotionalState(
        confidence=0.8,    # Dramatic self-assurance
        morale=0.6,       # Emotionally volatile
        trust=0.4,        # Dramatic trust issues
        aggression=0.7    # Bold when in the spotlight
    ),
    'K': EmotionalState(
        confidence=0.2,    # Deep insecurity masked by theory
        morale=0.4,       # Anxious about leadership
        trust=0.5,        # Desperately needs support
        aggression=0.3    # Cautious by nature
    ),
    'P': EmotionalState(
        confidence=0.5,    # Growing revolutionary spirit
        morale=0.8,       # Strong collective spirit (initially)
        trust=0.7,        # Solidarity with fellow pawns
        aggression=0.6    # Ready to challenge authority
    )
} 