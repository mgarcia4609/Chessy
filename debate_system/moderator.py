from typing import Dict, List, Optional
from dataclasses import dataclass
import chess

from piece_agents.base_agent import ChessPieceAgent
from piece_agents.personality_factory import PersonalityFactory
from chess_engine.sunfish_wrapper import SunfishEngine
from debate_system.protocols import (
    Position, 
    MoveProposal, 
    DebateRound,
    PersonalityConfig
)

class DebateModerator:
    """Manages the debate process between chess pieces"""
    
    def __init__(self, pieces: Dict[str, ChessPieceAgent]):
        self.pieces = pieces
        self.debate_history: List[DebateRound] = []

    @classmethod
    def create_default(cls, engine: SunfishEngine) -> 'DebateModerator':
        """Create a moderator with default pieces
        
        Each piece gets its own engine instance to allow for parallel analysis
        and different personality settings.
        """
        # Create personalities using the factory
        factory = PersonalityFactory()
        personalities = factory.create_all_personalities()
        
        # Create a separate engine instance for each piece
        pieces = {}
        for piece_type, personality in personalities.items():
            piece_engine = SunfishEngine.create_new()
            pieces[piece_type] = ChessPieceAgent(
                engine=piece_engine,
                personality=personality
            )

        return cls(pieces)
    
    @classmethod
    def create_themed(cls, engine: SunfishEngine, theme: str) -> 'DebateModerator':
        """Create a moderator with themed piece personalities
        
        Args:
            engine: Base engine instance
            theme: Theme to apply ('aggressive', 'defensive', 'creative')
        """
        factory = PersonalityFactory()
        pieces = {}
        
        for piece_type in ['P', 'N', 'B', 'R', 'Q', 'K']:
            personality = factory.create_themed_personality(piece_type, theme)
            piece_engine = SunfishEngine.create_new()
            pieces[piece_type] = ChessPieceAgent(
                engine=piece_engine,
                personality=personality
            )
            
        return cls(pieces)

    def get_proposals(self, position: Position, moves: List[str]) -> List[MoveProposal]:
        """Gather move proposals from all pieces that can move
        
        Args:
            position: Current chess position
            moves: List of legal moves in UCI format
        """
        proposals = []
        board = chess.Board(position.fen)
        
        for move_uci in moves:
            # Parse UCI move
            move = chess.Move.from_uci(move_uci)
            from_square = move.from_square
            
            # Get piece type at the from square
            piece = board.piece_at(from_square)
            if not piece or not piece.color == chess.WHITE:
                continue
                
            piece_type = piece.symbol().upper()
            if piece_type in self.pieces:
                agent = self.pieces[piece_type]
                proposal = agent.evaluate_move(position, move_uci)
                if proposal:
                    proposals.append(proposal)
        
        # Sort by score descending
        proposals.sort(key=lambda p: p.score, reverse=True)
        return proposals
    
    def conduct_debate(self, position: Position, moves: List[str]) -> DebateRound:
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
                f"{i+1}. {proposal.piece.personality.name}'s proposal "
                f"(score: {proposal.score:.2f}):\n"
                f"{proposal.argument}\n"
            )
        
        if debate.winning_proposal:
            summary_parts.append(
                f"\nWinning move: {debate.winning_proposal.piece.personality.name}'s proposal"
            )
        
        return "\n".join(summary_parts)
    
    def get_debate_history(self) -> List[str]:
        """Get a list of summaries for all past debates"""
        return [
            f"Turn {i+1}:\n{self.summarize_debate(debate)}"
            for i, debate in enumerate(self.debate_history)
        ] 