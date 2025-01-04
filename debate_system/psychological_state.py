from typing import Dict


class PsychologicalState:
    """Tracks overall board psychology"""
    
    def evaluate_team_state(self) -> Dict[str, float]:
        """Evaluate various team metrics"""
        return {
            'cohesion': self.calculate_team_cohesion(),
            'morale': self.calculate_team_morale(),
            'coordination': self.calculate_coordination_efficiency(),
            'leadership': self.identify_leadership_structure()
        }
    
    def simulate_psychological_impact(self, move: str) -> Dict[str, float]:
        """Predict how a move will affect team psychology"""
        impacts = {}
        
        # Material impact
        if self.is_capture(move):
            impacts['morale'] = -0.1  # Loss of material hurts morale
            
        # Position impact
        if self.is_retreat(move):
            impacts['confidence'] = -0.05
            
        # Relationship impact
        if self.is_sacrifice(move):
            piece = self.get_sacrificed_piece(move)
            impacts[f'trust_{piece}'] = -0.2
            
        return impacts