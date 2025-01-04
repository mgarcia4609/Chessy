from debate_system.protocols import DebateRound


class DebateImpact:
    """Tracks how debates affect team dynamics"""
    
    def record_debate_outcome(self, debate: DebateRound):
        winner = debate.winning_proposal.piece
        
        # Boost winner's confidence
        winner.emotional_state.confidence = min(1.0, 
            winner.emotional_state.confidence * 1.2)
        
        # Impact on other pieces
        for proposal in debate.proposals:
            if proposal.piece != winner:
                # Reduce confidence slightly
                proposal.piece.emotional_state.confidence *= 0.95
                
                # Trust impact based on argument quality
                agreement = self.calculate_argument_agreement(
                    winner.argument, proposal.argument)
                self.update_trust(winner, proposal.piece, agreement)

    def calculate_argument_agreement(self, arg1: str, arg2: str) -> float:
        """Use NLP to determine how much arguments agreed/disagreed"""
        # This could use sentiment analysis and semantic similarity
        pass