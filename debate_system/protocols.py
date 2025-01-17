"""Protocols and data structures for the debate chess system"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from piece_agents.base_agent import ChessPieceAgent
    from moderator import DebateModerator


class InteractionType(Enum):
    """Types of interactions between pieces"""
    SUPPORT = "support"           # One piece protects/supports another
    COOPERATION = "cooperation"   # Pieces working together in a tactic
    SACRIFICE = "sacrifice"       # One piece sacrificed for another's gain
    ABANDONMENT = "abandonment"   # One piece left another vulnerable
    RESCUE = "rescue"             # One piece saved another from capture
    COMPETITION = "competition"   # Pieces argued for different plans
    
    # Opponent-triggered interactions
    THREAT = "threat"             # A piece is put under direct attack
    TRAUMA = "trauma"             # A piece is captured (affects survivors)
    STALKING = "stalking"         # Repeated threats from same enemy piece
    BLOCKADE = "blockade"         # Being restricted/trapped by enemy pieces
    RIVALRY = "rivalry"           # Develops from repeated interactions with enemy

@dataclass
class EngineAnalysis:
    """Analysis results from the engine"""
    depth: int
    score: int
    pv: List[str]  # Principal variation (planned moves)
    nodes: int
    time_ms: int
    nps: int       # Nodes per second

@dataclass
class Interaction:
    """
    Record of an interaction between pieces
    Example: Knight sacrifices itself to save the queen
    
    interaction = Interaction(
        piece1="N",
        piece2="Q",
        type=InteractionType.SACRIFICE,
        turn=15,
        move="b5d6",  # Knight moves to be captured instead of queen
        impact=0.8,   # Very positive impact on relationship
        context="Sir Galahop valiantly intercepted the enemy bishop to protect Queen Dynamica"
    )
    
    This would significantly boost trust between them
    network.trust_matrix[("N", "Q")] += interaction.impact * 0.3
    """
    piece1: str
    piece2: str
    type: InteractionType
    turn: int
    move: str
    impact: float  # -1.0 to 1.0, negative for negative interactions
    context: str   # Description of what happened

@dataclass
class Trigger:
    """
    A position pattern that triggers an emotional response
    Example: Bishop gets traumatized by a fork

    trigger = Trigger(
        pattern="...N*b....",  # Enemy knight near bishop
        impacts={
            "confidence": -0.2,
            "aggression": -0.1
        },
        memory="Lost to a knight fork on d6",
        turn=12
    )

    Later, when a similar position occurs:

    if trigger.pattern in current_position.fen:
        bishop.emotional_state.apply_impact(trigger.impacts)
        argument = f"I'm wary of this position. {trigger.memory} still haunts me..."
    """
    pattern: str               # FEN-like pattern of relevant pieces
    impacts: Dict[str, float]  # Emotional impacts when pattern occurs
    memory: str                # Description of the associated memory
    turn: int                  # When this trigger was formed

@dataclass
class GameMoment:
    """
    A significant moment in the game
    Example: A successful queen sacrifice

    moment = GameMoment(
        position=position,
        move="d8h4",
        impact={
            "Q": {"confidence": 0.3, "aggression": 0.2},
            "N": {"morale": 0.2},
            "B": {"trust": 0.1}
        },
        turn=20,
        narrative="Queen Dynamica's brilliant sacrifice shattered the enemy kingside",
        participants=["Q", "N", "B"]
    )

    Later, when considering a sacrifice:

    relevant = memory.find_relevant_moments(
        piece="Q",
        pattern="sacrifice"
    )

    if relevant:
        confidence_bonus = sum(m.impact["Q"]["confidence"] 
                            for m in relevant) / len(relevant)
        queen.emotional_state.confidence += confidence_bonus
    """
    position: 'Position'      # The position when it happened
    move: str                 # The move that was played (UCI format)
    impact: Dict[str, float]  # Emotional impact on each piece
    turn: int                 # When it happened
    narrative: str            # Description of the moment
    participants: List[str]   # Pieces involved
    interaction_type: InteractionType = None  # Type of interaction if known

    @property
    def significance(self) -> float:
        """How significant this moment was (0-1)"""
        return min(1.0, sum(abs(v) for v in self.impact.values()) / len(self.impact))

@dataclass
class EmotionalState:
    """Current emotional state of a piece"""
    confidence: float = 0.5   # Affects risk-taking
    morale: float = 0.5       # Affects evaluation weights
    trust: float = 0.5        # Affects cooperation bonuses
    aggression: float = 0.5   # Affects tactical vs positional play
    
    def apply_impact(self, impact: Dict[str, float]):
        """Apply emotional impacts while keeping values in [0,1]"""
        for emotion, value in impact.items():
            current = getattr(self, emotion)
            new_value = max(0.0, min(1.0, current + value))
            setattr(self, emotion, new_value)
    
    @property
    def cooperation_bonus(self) -> float:
        """Higher trust and morale = better teamwork"""
        return (self.trust * self.morale) ** 0.5
    
    @property
    def risk_modifier(self) -> float:
        """Confidence and aggression affect risk-taking"""
        return (self.confidence * 0.7 + self.aggression * 0.3)

@dataclass
class Position:
    """Chess position representation"""
    fen: str
    move_history: List[str]  # UCI format moves
    
    @property
    def is_white_to_move(self) -> bool:
        """Determine if white to move based on FEN"""
        return self.fen.split()[1] == 'w'

@dataclass
class MoveProposal:
    """A proposed move from a piece"""
    piece: Dict[str, 'ChessPieceAgent']
    move: str  # UCI format (e.g. 'e2e4')
    score: float
    analysis: 'EngineAnalysis'
    argument: str
    interaction_type: Optional[InteractionType] = None
    tactical_context: Dict[str, bool] = field(default_factory=dict)  # captures, checks, etc
    affected_pieces: List[str] = field(default_factory=list)  # pieces involved in the move

@dataclass
class PsychologicalState:
    """Tracks overall board psychology"""
    cohesion: float = 0.5      # Team unity and coordination
    morale: float = 0.5        # Overall team spirit
    coordination: float = 0.5   # Tactical cooperation efficiency  
    leadership: float = 0.5     # Strength of leadership structure

    def evaluate_team_state(self) -> Dict[str, float]:
        """Evaluate various team metrics"""
        return {
            'cohesion': self.cohesion,
            'morale': self.morale, 
            'coordination': self.coordination,
            'leadership': self.leadership
        }

    def simulate_psychological_impact(self, proposal: MoveProposal) -> Dict[str, float]:
        """Predict how a move will affect team psychology"""
        if not proposal:
            return {}
        
        impacts = {}
        
        # Base impact on interaction type
        if proposal.interaction_type == InteractionType.SACRIFICE:
            impacts['morale'] = 0.2  # Heroic sacrifice boosts morale
            impacts['cohesion'] = 0.15  # Team admires the sacrifice
            
        elif proposal.interaction_type == InteractionType.COMPETITION:
            impacts['morale'] = -0.1  # Loss of material hurts morale
            impacts['cohesion'] = -0.05  # Some tension from the capture
            
        elif proposal.interaction_type == InteractionType.COOPERATION:
            impacts['coordination'] = 0.15  # Better tactical coordination
            impacts['cohesion'] = 0.1  # Working together builds trust
            
        elif proposal.interaction_type == InteractionType.SUPPORT:
            impacts['morale'] = 0.05  # Supporting moves boost spirits
            impacts['leadership'] = 0.1  # Good coordination shows leadership
            
        # Additional impacts based on tactical context
        if proposal.tactical_context.get('is_check'):
            impacts['confidence'] = 0.1  # Attacking the king boosts confidence
            
        if proposal.tactical_context.get('gives_discovered_attack'):
            impacts['coordination'] = 0.2  # Complex tactics show good coordination
            
        if proposal.tactical_context.get('is_promotion'):
            impacts['morale'] = 0.3  # Promotions are very exciting!
            
        return impacts

@dataclass
class DebateRound:
    """
    Records a round of debate
    Example: Strong agreement boosts team morale

    if debate.has_consensus:
        # All pieces agree, boost team spirit
        for piece in pieces.values():
            piece.emotional_state.apply_impact({
                "morale": 0.1,
                "trust": 0.05
            })

        narrative = "The pieces moved in perfect harmony, "
        narrative += "their shared vision strengthening their resolve."
    else:
        # Disagreement might cause tension
        for proposal in debate.proposals[1:]:
            proposal.piece.emotional_state.apply_impact({
                "trust": -0.05
            })
    """
    position: Position
    proposals: List[MoveProposal]
    winning_proposal: Optional[MoveProposal] = None
    
    @property
    def has_consensus(self) -> bool:
        """Check if there was strong agreement"""
        if len(self.proposals) < 2:
            return True
        
        # Check if top proposals are close in score
        top_score = self.proposals[0].score
        runner_up_score = self.proposals[1].score
        return abs(top_score - runner_up_score) < 0.2
    
    def apply_consensus_impact(self, psychological_state: PsychologicalState):
        """Apply consensus impact to overall board psychology"""
        psychological_state.cohesion += 0.1
        psychological_state.morale += 0.05
        psychological_state.coordination += 0.1
        psychological_state.leadership += 0.05
        
@dataclass
class PersonalityConfig:
    """Configuration for engine personality"""
    name: str
    description: str
    options: Dict[str, int]         # Engine option name -> value
    
    tactical_weight: float = 1.0    # Weight for tactical evaluation
    positional_weight: float = 1.0  # Weight for positional factors
    risk_tolerance: float = 0.5     # 0 = very cautious, 1 = very aggressive

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

@dataclass
class RelationshipNetwork:
    """Tracks relationships between pieces"""
    trust_matrix: Dict[Tuple[str, str], float] = field(default_factory=dict)  # (piece1, piece2) -> trust level
    recent_interactions: List[Interaction] = field(default_factory=list)  # Last N interactions
    
    def get_support_bonus(self, piece1: str, piece2: str) -> float:
        """Calculate bonus for pieces working together"""
        trust = self.trust_matrix.get((piece1, piece2), 0.5)
        recent = self.get_recent_cooperation(piece1, piece2)
        return trust * (1 + recent * 0.5)  # Recent cooperation amplifies trust
        
    def get_recent_cooperation(self, piece1: str, piece2: str, window: int = 5) -> float:
        """Calculate recent cooperation level between pieces"""
        if not self.recent_interactions:
            return 0.0
            
        # Look at last N interactions involving these pieces
        relevant = [
            i for i in self.recent_interactions[-window:]
            if (i.piece1 == piece1 and i.piece2 == piece2) or
               (i.piece1 == piece2 and i.piece2 == piece1)
        ]
        
        if not relevant:
            return 0.0
            
        # Calculate average impact of cooperative interactions
        cooperative = [i for i in relevant if i.type in 
                      (InteractionType.COOPERATION, InteractionType.SUPPORT)]
        if not cooperative:
            return 0.0
            
        return sum(i.impact for i in cooperative) / len(cooperative)

@dataclass
class PieceInteractionObserver:
    """Observes and tracks interactions for a specific chess piece"""
    piece: 'ChessPieceAgent'
    relationship_network: RelationshipNetwork
    
    def on_game_moment(self, moment: GameMoment):
        """React to a game moment by updating piece emotional state"""
        # Only react if this piece is involved
        piece_type = self.piece.personality.name[0].upper()  # Get piece type from name
        if piece_type in moment.impact:
            self.piece.emotional_state.apply_impact(moment.impact[piece_type])
            
    def on_relationship_change(self, piece1: str, piece2: str, change: float):
        """React to relationship changes involving this piece"""
        piece_type = self.piece.personality.name[0].upper()
        if piece1 == piece_type or piece2 == piece_type:
            # Update emotional state based on relationship change
            trust_impact = {"trust": change * 0.5}
            self.piece.emotional_state.apply_impact(trust_impact)
            
            # Get cooperation bonus from relationship network
            other_piece = piece2 if piece1 == piece_type else piece1
            bonus = self.relationship_network.get_support_bonus(piece_type, other_piece)
            
            # Apply cooperation bonus to morale
            if bonus > 0:
                self.piece.emotional_state.apply_impact({"morale": bonus * 0.3})

class PersonalityTrait(Enum):
    """Core personality traits that influence behavior and interactions"""
    DRAMATIC = "dramatic"           # Queen's flair, Knight's quests
    ANALYTICAL = "analytical"       # Bishop's preaching, King's theories
    PROTECTIVE = "protective"       # Rook's fortresses, King's safety
    REVOLUTIONARY = "revolutionary" # Pawn's ambitions
    ADVENTUROUS = "adventurous"     # Knight's quests
    NEUROTIC = "neurotic"           # King's anxiety, Rook's agoraphobia
    ZEALOUS = "zealous"             # Bishop's conversion attempts
    THEATRICAL = "theatrical"       # Queen's drama

@dataclass
class InteractionProfile:
    """Defines how a piece tends to interact with others"""
    primary_traits: List[PersonalityTrait]
    cooperation_style: str  # How they work with others
    conflict_style: str     # How they handle disagreements
    leadership_style: str   # How they influence others

@dataclass
class GameMemory:
    """Tracks significant game events and their emotional impact"""
    key_moments: List[GameMoment] = field(default_factory=list)
    narrative_threads: Dict[str, List[str]] = field(default_factory=dict)
    emotional_triggers: Dict[str, List[Trigger]] = field(default_factory=dict)
    
    def record_moment(self, position: Position, move: str, 
                     emotional_impact: Dict[str, float]):
        """Record a significant game moment"""
        moment = GameMoment(
            position=position,
            move=move,
            impact=emotional_impact,
            turn=len(self.key_moments) + 1,
            narrative="",  # Will be generated
            participants=[]  # Will be determined
        )
        self.key_moments.append(moment)
        
        # Update narrative threads
        piece = move[0]  # Get piece type from move
        if piece not in self.narrative_threads:
            self.narrative_threads[piece] = []
        self.narrative_threads[piece].append(
            self.generate_moment_narrative(moment))
        
        # Update emotional triggers
        if abs(max(emotional_impact.values())) > 0.2:
            if piece not in self.emotional_triggers:
                self.emotional_triggers[piece] = []
            self.emotional_triggers[piece].append(
                Trigger(
                    pattern=position.fen,  # Simplified for now
                    impacts=emotional_impact,
                    memory=self.generate_moment_narrative(moment),
                    turn=len(self.key_moments)
                )
            )
    
    def generate_moment_narrative(self, moment: GameMoment) -> str:
        """Generate narrative description of a moment"""
        # Simplified for now
        return f"Turn {moment.turn}: Move {moment.move} played"
    
    def generate_argument_context(self, piece: str, 
                                position: Position) -> str:
        """Generate contextual argument based on piece's history"""
        # Get piece's narrative thread
        thread = self.narrative_threads.get(piece, [])
        
        # Get relevant triggers
        triggers = self.emotional_triggers.get(piece, [])
        active_triggers = [
            t for t in triggers
            if t.pattern in position.fen  # Simplified pattern matching
        ]
        
        # Combine into context
        context = []
        if thread:
            context.append(f"Remembering: {thread[-1]}")
        if active_triggers:
            context.append(f"Feeling: {active_triggers[-1].memory}")
            
        return " ".join(context) if context else ""



@dataclass
class LLMContext:
    """Context bundle for LLM character inference"""
    personality_template: PersonalityTemplate
    recent_interactions: List[Interaction]
    game_memory: GameMemory
    psychological_state: PsychologicalState
    debate_history: List[DebateRound]

@dataclass
class TeamPsychologyObserver:
    """Observes game moments and updates team psychological state"""
    moderator: 'DebateModerator'  # Reference to the moderator that owns the psychological state
    
    def on_game_moment(self, moment: GameMoment):
        """React to game moments by updating team psychological state"""
        # Calculate team impact based on event type and significance
        interaction_type = moment.interaction_type
        if interaction_type == InteractionType.TRAUMA:
            # Major trauma affects whole team
            self.moderator.psychological_state.morale = max(0.0, min(1.0, self.moderator.psychological_state.morale - 0.2))
            self.moderator.psychological_state.cohesion = max(0.0, min(1.0, self.moderator.psychological_state.cohesion - 0.1))
            self.moderator.psychological_state.cohesion = max(0.0, min(1.0, self.moderator.psychological_state.cohesion - 0.1))
            self.moderator.psychological_state.coordination = max(0.0, min(1.0, self.moderator.psychological_state.coordination - 0.1))
            self.moderator.psychological_state.leadership = max(0.0, min(1.0, self.moderator.psychological_state.leadership - 0.05))
        elif interaction_type == InteractionType.THREAT:
            # Threats can sometimes unite the team
            self.moderator.psychological_state.morale = max(0.0, min(1.0, self.moderator.psychological_state.morale - 0.1))
            self.moderator.psychological_state.cohesion = max(0.0, min(1.0, self.moderator.psychological_state.cohesion + 0.1))
            
    def on_relationship_change(self, piece1: str, piece2: str, change: float):
        """React to relationship changes by updating team cohesion"""
        # Significant relationship changes affect team cohesion
        if abs(change) > 0.3:
            self.moderator.psychological_state.cohesion = max(0.0, min(1.0, 
                self.moderator.psychological_state.cohesion + (change * 0.2)))