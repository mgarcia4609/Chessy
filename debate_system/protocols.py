"""Protocols and data structures for the debate chess system"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class InteractionType(Enum):
    """Types of interactions between pieces"""
    SUPPORT = "support"           # One piece protects/supports another
    COOPERATION = "cooperation"   # Pieces working together in a tactic
    SACRIFICE = "sacrifice"       # One piece sacrificed for another's gain
    ABANDONMENT = "abandonment"   # One piece left another vulnerable
    RESCUE = "rescue"             # One piece saved another from capture
    COMPETITION = "competition"   # Pieces argued for different plans

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
    move: str  # UCI format (e.g. 'e2e4')
    score: float
    analysis: 'EngineAnalysis'
    argument: str

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

class RelationshipNetwork:
    """Tracks relationships between pieces"""
    trust_matrix: Dict[Tuple[str, str], float]  # (piece1, piece2) -> trust level
    recent_interactions: List[Interaction]  # Last N interactions
    
    def get_support_bonus(self, piece1: str, piece2: str) -> float:
        """Calculate bonus for pieces working together"""
        trust = self.trust_matrix.get((piece1, piece2), 0.5)
        recent = self.get_recent_cooperation(piece1, piece2)
        return trust * (1 + recent * 0.5)  # Recent cooperation amplifies trust

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
    
    key_moments: List[GameMoment]
    narrative_threads: Dict[str, List[str]]  # Piece -> their story
    emotional_triggers: Dict[str, List[Trigger]]  # What affects each piece
    
    def record_moment(self, position: Position, move: str, 
                     emotional_impact: Dict[str, float]):
        """Record a significant game moment"""
        moment = GameMoment(
            position=position,
            move=move,
            impact=emotional_impact,
            turn=len(self.key_moments) + 1
        )
        self.key_moments.append(moment)
        
        # Update narrative threads
        piece = self.get_moving_piece(move)
        self.narrative_threads[piece].append(
            self.generate_moment_narrative(moment))
        
        # Update emotional triggers
        if abs(max(emotional_impact.values())) > 0.2:
            self.emotional_triggers[piece].append(
                Trigger(position.pattern, emotional_impact))
    
    def generate_argument_context(self, piece: str, 
                                position: Position) -> str:
        """Generate contextual argument based on piece's history"""
        relevant_moments = self.find_relevant_moments(piece, position)
        emotional_state = self.calculate_current_emotion(piece)
        
        return self.generate_narrative(
            piece, relevant_moments, emotional_state)

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

@dataclass
class LLMContext:
    """Context bundle for LLM character inference"""
    personality_template: PersonalityTemplate
    recent_interactions: List[Interaction]
    game_memory: GameMemory
    psychological_state: PsychologicalState
    debate_history: List[DebateRound]