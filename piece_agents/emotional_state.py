from dataclasses import dataclass


@dataclass
class EmotionalState:
    # Base emotions (0-1 scale)
    confidence: float
    morale: float
    trust: float
    aggression: float
    
    # Derived states
    @property
    def cooperation_bonus(self) -> float:
        """Higher trust and morale = better teamwork"""
        return (self.trust * self.morale) ** 0.5
    
    @property
    def risk_modifier(self) -> float:
        """Confidence and aggression affect risk-taking"""
        return (self.confidence * 0.7 + self.aggression * 0.3)