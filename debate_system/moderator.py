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
    InteractionType,
    PsychologicalState,
    GameMemory,
    RelationshipNetwork,
    TeamPsychologyObserver
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

    def register_opponent_action(self, position: Position, move: str, 
                               affected_pieces: List[str], interaction_type: InteractionType,
                               turn: int):
        """Record an opponent's action and its impact on our pieces
        
        Args:
            position: Current chess position
            move: The opponent's move in UCI format
            affected_pieces: List of our pieces affected by the move (e.g. ["Pe4"])
            interaction_type: Type of interaction (THREAT, TRAUMA, etc)
            turn: Current turn number
        """
        # Determine impact based on interaction type
        if interaction_type == InteractionType.TRAUMA:
            impact = -0.5  # Major negative impact for captures
        elif interaction_type == InteractionType.THREAT:
            impact = -0.3  # Moderate negative impact for threats
        elif interaction_type == InteractionType.STALKING:
            impact = -0.2  # Minor negative impact for repeated threats
        else:
            impact = -0.1  # Default negative impact
            
        # Create context description based on type
        context_map = {
            InteractionType.TRAUMA: "was captured by",
            InteractionType.THREAT: "is threatened by",
            InteractionType.STALKING: "is being stalked by",
            InteractionType.BLOCKADE: "is blocked by",
            InteractionType.RIVALRY: "faces rivalry from"
        }
        action = context_map.get(interaction_type, "interacts with")
        
        # Record interaction for each affected piece
        for piece_id in affected_pieces:
            interaction = Interaction(
                piece1=piece_id,
                piece2=f"black_{move[2:4]}",  # Use destination square to identify enemy piece
                type=interaction_type,
                turn=turn,
                move=move,
                impact=impact,
                context=f"{piece_id} {action} enemy piece on {move[2:4]}"
            )
            self.register_interaction(interaction)
            
            # Create game moment for significant events
            if interaction_type in [InteractionType.TRAUMA, InteractionType.THREAT]:
                moment = GameMoment(
                    position=position,
                    move=move,
                    impact={piece_id[0]: {
                        "confidence": impact * 0.05,
                        "morale": impact * 0.5,
                    }},
                    turn=turn,
                    narrative=interaction.context,
                    participants=[piece_id],
                    interaction_type = interaction_type
                )
                self.notify_moment(moment)


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
        
    def _find_piece_agent(self, piece_type: str, square_name: str, pieces: Dict[str, ChessPieceAgent]) -> Optional[ChessPieceAgent]:
        """Find a piece agent by its type and current square.
        
        Args:
            piece_type: Type of piece (e.g., 'N' for knight)
            square_name: Current square name (e.g., 'f3')
            pieces: Dictionary of piece agents
            
        Returns:
            The piece agent if found, None otherwise
        """
        target_square = chess.parse_square(square_name)
        
        # Look for a piece of the right type at the target square
        for agent in pieces.values():
            if (agent.board_piece and 
                agent.board_piece.symbol().upper() == piece_type and 
                chess.square_name(agent.square) == square_name):
                return agent
                
        return None

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
                print(f"No piece at {from_square}")
                continue
                
            piece_type = piece.symbol().upper()
            square_name = chess.square_name(from_square)
            
            agent = self._find_piece_agent(piece_type, square_name, pieces)
            agent_id = agent.piece_id
            if agent:
                proposal = agent.evaluate_move(position, move_uci, agent_id)
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
            
        # Register team psychology observer
        team_observer = TeamPsychologyObserver(
            moderator=self
        )
        self.interaction_mediator.register(team_observer)

    @classmethod
    def create_default(cls, engine: ChessEngine) -> 'DebateModerator':
        """Create a moderator with default pieces"""
        factory = PersonalityFactory()
        personalities = factory.create_all_personalities()
        pieces = PieceAgentFactory.create_all_agents(personalities, engine)
        return cls(pieces)
    
    @classmethod
    def create_themed(cls, engine: ChessEngine, theme: str) -> 'DebateModerator':
        """Create a moderator with themed piece personalities"""
        factory = PersonalityFactory()
        personalities = {
            piece_type: factory.create_themed_personality(piece_type, theme)
            for piece_type in ['P', 'N', 'B', 'R', 'Q', 'K']
        }
        pieces = PieceAgentFactory.create_all_agents(personalities, engine)
        return cls(pieces)

    def conduct_debate(self, position: Position, moves: List[str]) -> DebateRound:
        """Conduct a debate round using command pattern"""
        # Update piece positions based on move history
        self.update_piece_positions(position.move_history)
        
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
            print("No proposals to choose from")
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
            piece_agent = next(iter(proposal.piece.values()))
            summary_parts.append(
                f"{i+1}. {piece_agent.personality.name}'s proposal "
                f"(score: {proposal.score:.2f}):\n"
                f"{proposal.argument}\n"
            )
        
        if debate.winning_proposal:
            piece_agent = next(iter(debate.winning_proposal.piece.values()))
            summary_parts.append(
                f"\nWinning move: {piece_agent.personality.name}'s proposal"
            )
        
        return "\n".join(summary_parts)
    
    def get_debate_history(self) -> List[str]:
        """Get a list of summaries for all past debates"""
        return [
            f"Turn {i+1}:\n{self.summarize_debate(debate)}"
            for i, debate in enumerate(self.debate_history)
        ] 
    
    def update_piece_positions(self, move_history: List[str]):
        """Update piece positions based on move history.
        
        Args:
            move_history: List of moves in UCI format (e.g. ['e2e4', 'e7e5'])
        """
        # Start from initial position
        board = chess.Board()
        
        # Replay moves and update piece positions
        for move_uci in move_history:
            move = chess.Move.from_uci(move_uci)
            
            # Only track white pieces
            piece = board.piece_at(move.from_square)
            if piece and piece.color == chess.WHITE:
                self._update_piece_position(piece, move)
                
            # Make the move on our tracking board
            board.push(move)
    
    def _update_piece_position(self, piece: chess.Piece, move: chess.Move):
        """Update a piece's position when it moves.
        
        Args:
            piece: The chess piece that moved
            move: The move that was made
        """
        piece_type = piece.symbol().upper()
        
        # Find the agent for this piece
        for agent in self.pieces.values():
            if (agent.board_piece and 
                agent.board_piece.symbol().upper() == piece_type and 
                agent.square == move.from_square):
                # Update the agent's square to the new position
                agent.square = move.to_square
                break 