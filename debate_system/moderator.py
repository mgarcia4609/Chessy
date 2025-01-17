import chess
from dataclasses import dataclass
from typing import Dict, List, Protocol, Optional
from abc import ABC, abstractmethod

from chess_engine.sunfish_wrapper import ChessEngine
from debate_system.protocols import (
    DebateRound,
    MoveProposal,
    PieceInteractionObserver,
    Position,
    GameMoment,
    EmotionalState,
    Interaction,
    PsychologicalState,
    GameMemory,
    RelationshipNetwork
)
from piece_agents.base_agent import ChessPieceAgent
from piece_agents.personality_factory import PersonalityFactory
from piece_agents.piece_factory import PieceAgentFactory


@dataclass
class AgentMemento:
    """Captures and restores agent state"""
    personality_state: Dict
    emotional_state: EmotionalState
    interaction_history: List[Interaction]
    timestamp: int


class AgentCaretaker:
    """Manages agent state history"""
    def __init__(self):
        self.history: Dict[str, List[AgentMemento]] = {}  # piece_type -> history
        
    def save_state(self, piece_type: str, agent: ChessPieceAgent, turn: int):
        """Save agent state at given turn"""
        if piece_type not in self.history:
            self.history[piece_type] = []
            
        memento = AgentMemento(
            personality_state=agent.personality,
            emotional_state=agent.emotional_state,
            interaction_history=agent._recent_interactions,
            timestamp=turn
        )
        self.history[piece_type].append(memento)
        
    def restore_state(self, piece_type: str, turn: int) -> Optional[AgentMemento]:
        """Restore agent state from specific turn"""
        if piece_type not in self.history:
            return None
            
        # Find closest state before or at given turn
        states = sorted(self.history[piece_type], key=lambda x: x.timestamp)
        for state in reversed(states):
            if state.timestamp <= turn:
                return state
        return None


class InteractionObserver(Protocol):
    """Protocol for pieces that observe interactions"""
    def on_game_moment(self, moment: GameMoment): ...
    def on_relationship_change(self, piece1: str, piece2: str, change: float): ...


class InteractionMediator:
    """Manages and coordinates piece interactions"""
    def __init__(self):
        self._observers: List[InteractionObserver] = []
        self.relationship_network = RelationshipNetwork()
        
    def register(self, observer: InteractionObserver):
        """Register an observer for interactions"""
        self._observers.append(observer)
        
    def notify_moment(self, moment: GameMoment):
        """Notify all observers of a game moment"""
        for observer in self._observers:
            observer.on_game_moment(moment)
            
    def notify_relationship(self, piece1: str, piece2: str, change: float):
        """Notify all observers of a relationship change"""
        for observer in self._observers:
            observer.on_relationship_change(piece1, piece2, change)
            
    def register_interaction(self, interaction: Interaction):
        """Record an interaction and update relationships"""
        self.relationship_network.recent_interactions.append(interaction)
        
        # Update trust matrix
        trust_change = interaction.impact * 0.3
        self.relationship_network.trust_matrix[(interaction.piece1, interaction.piece2)] = trust_change
        
        # Notify observers
        self.notify_relationship(interaction.piece1, interaction.piece2, trust_change)


class DebateStrategy(ABC):
    """Abstract strategy for conducting debates"""
    @abstractmethod
    def conduct_debate(self, position: Position, pieces: Dict[str, ChessPieceAgent],
                      moves: List[str]) -> DebateRound: ...


class StandardDebate(DebateStrategy):
    """Standard debate implementation"""
    def conduct_debate(self, position: Position, pieces: Dict[str, ChessPieceAgent],
                      moves: List[str]) -> DebateRound:
        """Conduct standard debate process"""
        proposals = self._gather_proposals(position, pieces, moves)
        return DebateRound(position=position, proposals=proposals)
        
    def _gather_proposals(self, position: Position, pieces: Dict[str, ChessPieceAgent],
                         moves: List[str]) -> List[MoveProposal]:
        """Gather move proposals from all pieces that can move"""
        proposals = []
        board = chess.Board(position.fen)
        
        for move_uci in moves:
            move = chess.Move.from_uci(move_uci)
            from_square = move.from_square

            piece = board.piece_at(from_square)
            if not piece or not piece.color == chess.WHITE:
                continue
                
            piece_type = piece.symbol().upper()
            if piece_type in pieces:
                agent = pieces[piece_type]
                proposal = agent.evaluate_move(position, move_uci)
                if proposal:
                    proposals.append(proposal)
        
        proposals.sort(key=lambda p: p.score, reverse=True)
        return proposals


class DebateCommand:
    """Command pattern for debate actions"""
    def __init__(self, moderator: 'DebateModerator', strategy: DebateStrategy):
        self.moderator = moderator
        self.strategy = strategy
        
    def execute(self, position: Position, moves: List[str]) -> DebateRound:
        """Execute the debate command"""
        return self.strategy.conduct_debate(
            position, self.moderator.pieces, moves)


class DebateModerator:
    """Manages the debate process between chess pieces"""
    
    def __init__(self, pieces: Dict[str, ChessPieceAgent]):
        self.interaction_mediator = InteractionMediator()
        self.debate_strategy = StandardDebate()
        self.psychological_state = PsychologicalState()
        self.game_memory = GameMemory()
        self.caretaker = AgentCaretaker()
        self.debate_history: List[DebateRound] = []
        
        # Initialize pieces
        self.pieces = pieces
        
        # Create and register observers for each piece
        for piece in pieces.values():
            observer = PieceInteractionObserver(
                piece=piece,
                relationship_network=self.interaction_mediator.relationship_network
            )
            self.interaction_mediator.register(observer)

    @classmethod
    def create_default(cls, engine: ChessEngine) -> 'DebateModerator':
        """Create a moderator with default pieces"""
        factory = PersonalityFactory()
        personalities = factory.create_all_personalities()
        
        # Create concrete piece agents
        pieces = PieceAgentFactory.create_all_agents(personalities, engine)
        return cls(pieces)
    
    @classmethod
    def create_themed(cls, engine: ChessEngine, theme: str) -> 'DebateModerator':
        """Create a moderator with themed piece personalities"""
        factory = PersonalityFactory()
        pieces = {}
        
        for piece_type in ['P', 'N', 'B', 'R', 'Q', 'K']:
            personality = factory.create_themed_personality(piece_type, theme)
            pieces[piece_type] = PieceAgentFactory.create_agent(
                piece_type, personality, ChessEngine()
            )
            
        return cls(pieces)

    def conduct_debate(self, position: Position, moves: List[str]) -> DebateRound:
        """Conduct a debate round using command pattern"""
        command = DebateCommand(self, self.debate_strategy)
        debate = command.execute(position, moves)
        
        # Save piece states
        for piece_type, piece in self.pieces.items():
            self.caretaker.save_state(piece_type, piece, len(self.debate_history))
        
        # Choose winning proposal
        debate = self.choose_winning_proposal(debate)
        
        # Record debate and update memory
        self.debate_history.append(debate)
        if debate.winning_proposal:  # Only record moment if we have a winning proposal
            self.game_memory.record_moment(
                position=position,
                move=debate.winning_proposal.move,
                emotional_impact=self.psychological_state.simulate_psychological_impact(debate.winning_proposal)
            )
        
        return debate
    
    def choose_winning_proposal(self, debate: DebateRound) -> DebateRound:
        """Assign a winning proposal to a DebateRound object based on highest score for now"""
        if not debate.proposals:
            return None
            
        # Sort proposals by score (highest first)
        sorted_proposals = sorted(debate.proposals, key=lambda p: p.score, reverse=True)
        
        # Select the highest scoring proposal
        winning_proposal = sorted_proposals[0]
        
        # Update the debate with the winning proposal
        debate.winning_proposal = winning_proposal
        
        if debate.has_consensus:
            debate.apply_consensus_impact(self.psychological_state)
        
        return debate
    
    def select_winning_proposal(self, debate: DebateRound, choice_idx: int) -> MoveProposal:
        """Select a winning proposal and update relationships"""
        if not 0 <= choice_idx < len(debate.proposals):
            raise ValueError(f"Invalid choice index: {choice_idx}")
        
        winning_proposal = debate.proposals[choice_idx]
        debate.winning_proposal = winning_proposal
        
        # Register interaction for winning move
        # Use affected_pieces from the proposal for piece types
        piece1 = winning_proposal.affected_pieces[0] if winning_proposal.affected_pieces else None
        piece2 = winning_proposal.affected_pieces[1] if len(winning_proposal.affected_pieces) > 1 else None
        
        if piece1:  # Only register if we have at least one piece involved
            self.interaction_mediator.register_interaction(
                Interaction(
                    piece1=piece1,
                    piece2=piece2 if piece2 else piece1,  # Default to same piece if no second piece
                    type=winning_proposal.interaction_type,
                    turn=len(self.debate_history),
                    move=winning_proposal.move,
                    impact=0.2 if choice_idx == 0 else -0.1,
                    context=winning_proposal.argument
                )
            )
        
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