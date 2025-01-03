from typing import Dict, List, Optional
from dataclasses import dataclass
from piece_agents.base_agent import ChessPieceAgent
from piece_agents.knight import KnightAgent
from sunfish import Position, Move

@dataclass
class MoveProposal:
    """A proposed move from a piece"""
    piece: ChessPieceAgent
    move: Move
    score: float
    argument: str

@dataclass
class DebateRound:
    """Records a round of debate"""
    position: Position
    proposals: List[MoveProposal]
    winning_proposal: Optional[MoveProposal] = None

class DebateModerator:
    """Manages the debate process between chess pieces"""
    
    def __init__(self, pieces: Dict[str, ChessPieceAgent]):
        self.pieces = pieces
        self.debate_history: List[DebateRound] = []
    
    @classmethod
    def create_default(cls) -> 'DebateModerator':
        """Create a moderator with default pieces"""
        pieces = {
            'N': KnightAgent("Sir Galahop"),
            # Add other pieces here as they are implemented
        }
        return cls(pieces)
    
    def get_proposals(self, position: Position, moves: List[Move]) -> List[MoveProposal]:
        """Gather move proposals from all pieces that can move"""
        proposals = []
        
        for move in moves:
            piece = position.board[move.i].upper()
            if piece in self.pieces:
                agent = self.pieces[piece]
                score = agent.evaluate_move(position, move)
                argument = agent.generate_argument(position, move, score)
                
                proposals.append(MoveProposal(
                    piece=agent,
                    move=move,
                    score=score,
                    argument=argument
                ))
        
        # Sort by score descending
        proposals.sort(key=lambda p: p.score, reverse=True)
        return proposals
    
    def conduct_debate(self, position: Position, moves: List[Move]) -> DebateRound:
        """Conduct a debate round and return the results"""
        proposals = self.get_proposals(position, moves)
        debate = DebateRound(position=position, proposals=proposals)
        self.debate_history.append(debate)
        return debate
    
    def select_winning_proposal(self, debate: DebateRound, choice_idx: int) -> MoveProposal:
        """Select a winning proposal from the debate"""
        if not 0 <= choice_idx < len(debate.proposals):
            raise ValueError(f"Invalid choice index: {choice_idx}")
        
        winning_proposal = debate.proposals[choice_idx]
        debate.winning_proposal = winning_proposal
        return winning_proposal
    
    def summarize_debate(self, debate: DebateRound) -> str:
        """Generate a summary of the debate round"""
        summary_parts = []
        
        for i, proposal in enumerate(debate.proposals):
            summary_parts.append(
                f"{i+1}. {proposal.piece.name}'s proposal "
                f"(score: {proposal.score:.2f}):\n"
                f"{proposal.argument}\n"
            )
        
        if debate.winning_proposal:
            summary_parts.append(
                f"\nWinning move: {debate.winning_proposal.piece.name}'s proposal"
            )
        
        return "\n".join(summary_parts)
    
    def get_debate_history(self) -> List[str]:
        """Get a list of summaries for all past debates"""
        return [
            f"Turn {i+1}:\n{self.summarize_debate(debate)}"
            for i, debate in enumerate(self.debate_history)
        ] 