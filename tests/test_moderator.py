import pytest
import chess
from typing import TYPE_CHECKING
from debate_system.protocols import (
    Position, MoveProposal, EmotionalState,
    Interaction, InteractionType, DebateRound
)
from chess_engine.sunfish_wrapper import ChessEngine
from debate_system.moderator import DebateModerator
from piece_agents.personality_factory import PersonalityFactory
if TYPE_CHECKING:
    from chess_engine.sunfish_wrapper import ChessEngine
    from debate_system.moderator import DebateModerator
    from piece_agents.personality_factory import PersonalityFactory


@pytest.fixture
def engine():
    """Create a fresh engine instance for each test"""
    return ChessEngine()

@pytest.fixture
def factory():
    """Create personality factory"""
    return PersonalityFactory()

@pytest.fixture
def default_moderator(engine):
    """Create a moderator with default personalities"""
    return DebateModerator.create_default(engine)

@pytest.fixture
def aggressive_moderator(engine):
    """Create a moderator with aggressive personalities"""
    return DebateModerator.create_themed(engine, "aggressive")

@pytest.fixture
def starting_position():
    """Create a starting position"""
    return Position(
        fen=chess.STARTING_FEN,
        move_history=[]
    )

def test_create_default_moderator(default_moderator):
    """Test creating moderator with default personalities"""
    # Check all piece types are present
    print(default_moderator.pieces.keys())
    assert set(default_moderator.pieces.keys()) == {'Ph2', 'Pg2', 'Pf2', 'Pe2', 'Pd2', 'Pc2', 'Pb2', 'Pa2', 'Rh1', 'Ng1', 'Bf1', 'Ke1', 'Qd1', 'Bc1', 'Nb1', 'Ra1'}
    
    # Verify piece personalities
    knight = default_moderator.pieces['Nb1']
    assert "modern Don Quixote" in knight.personality.description
    assert knight.personality.tactical_weight == 1.2
    
    queen = default_moderator.pieces['Qd1']
    assert "drama queen" in queen.personality.description
    assert queen.personality.risk_tolerance > 0.5

def test_create_themed_moderator(aggressive_moderator):
    """Test creating moderator with themed personalities"""
    # Check personality modifications
    knight = aggressive_moderator.pieces['Nb1']
    assert knight.personality.tactical_weight > 1.2  # More aggressive than default
    assert "aggressively" in knight.personality.description.lower()
    
    bishop = aggressive_moderator.pieces['Bc1']
    assert bishop.personality.risk_tolerance > 0.5
    assert "zealously" in bishop.personality.description.lower()

def test_basic_debate_flow(default_moderator, starting_position):
    """Test basic debate process"""
    # Get legal moves for white's first move
    moves = ["e2e4", "d2d4", "g1f3"]
    
    # Conduct debate
    debate = default_moderator.conduct_debate(starting_position, moves)
    
    assert isinstance(debate, DebateRound)
    assert len(debate.proposals) > 0
    assert all(isinstance(p, MoveProposal) for p in debate.proposals)
    
    # Verify proposals are sorted by score
    scores = [p.score for p in debate.proposals]
    assert scores == sorted(scores, reverse=True)

def test_winning_proposal_selection(default_moderator, starting_position):
    """Test selecting winning proposal affects relationships"""
    moves = ["e2e4", "d2d4"]
    debate = default_moderator.conduct_debate(starting_position, moves)
    
    # Select first proposal as winner
    winning = default_moderator.select_winning_proposal(debate, 0)
    
    # Verify interaction was recorded
    mediator = default_moderator.interaction_mediator
    assert len(mediator.relationship_network.recent_interactions) > 0
    
    # Verify it was recorded as support
    last_interaction = mediator.relationship_network.recent_interactions[-1]
    assert last_interaction.type == InteractionType.SUPPORT
    assert last_interaction.impact > 0

def test_opponent_interaction_types():
    """Test that opponent interactions are properly typed"""
    # Create a simple interaction for each opponent type
    threat = Interaction(
        piece1="e2",  # White pawn
        piece2="black_knight",  # Enemy piece
        type=InteractionType.THREAT,
        turn=1,
        move="g1f3",  # Knight threatens pawn
        impact=-0.3,  # Negative impact on confidence
        context="Enemy knight threatens our pawn"
    )
    assert threat.type == InteractionType.THREAT
    assert threat.impact < 0
    
    trauma = Interaction(
        piece1="e4",  # White pawn
        piece2="black_knight",
        type=InteractionType.TRAUMA,
        turn=2,
        move="f6e4",  # Knight captures pawn
        impact=-0.5,  # Major negative impact
        context="Our pawn was captured by the enemy knight"
    )
    assert trauma.type == InteractionType.TRAUMA
    assert trauma.impact < threat.impact  # Trauma should be more impactful than threat
    
    stalking = Interaction(
        piece1="f3",  # White knight
        piece2="black_bishop",
        type=InteractionType.STALKING,
        turn=3,
        move="c8h3",  # Bishop repeatedly targeting knight
        impact=-0.2,  # Moderate negative impact
        context="That bishop keeps threatening our knight"
    )
    assert stalking.type == InteractionType.STALKING
    assert -0.5 < stalking.impact < 0  # Moderate negative impact

def test_register_opponent_action(default_moderator, starting_position):
    """Test registering opponent actions affects piece relationships and emotions"""
    # Setup: Make a move to e4 first
    moves = ["e2e4"]
    debate = default_moderator.conduct_debate(starting_position, moves)
    winning = default_moderator.select_winning_proposal(debate, 0)
    
    # Record initial states
    initial_team_morale = default_moderator.psychological_state.morale
    initial_team_cohesion = default_moderator.psychological_state.cohesion
    pawn = default_moderator.pieces["Pe2"]
    initial_pawn_confidence = pawn.emotional_state.confidence
    initial_pawn_morale = pawn.emotional_state.morale
    print(f"initial_pawn_confidence: {initial_pawn_confidence}")
    print(f"initial_pawn_morale: {initial_pawn_morale}")
    
    # Record black's threatening move
    mediator = default_moderator.interaction_mediator
    mediator.register_opponent_action(
        position=starting_position,
        move="f7f6",  # Black pawn moves to threaten e4
        affected_pieces=["Pe2"],  # Our pawn is referenced by starting square
        interaction_type=InteractionType.THREAT,
        turn=1
    )
    
    # Verify interaction was recorded
    last_interaction = mediator.relationship_network.recent_interactions[-1]
    assert last_interaction.type == InteractionType.THREAT
    assert last_interaction.impact < 0
    
    # Verify individual piece impact from threat
    assert pawn.emotional_state.confidence < initial_pawn_confidence  # Confidence drops
    assert pawn.emotional_state.morale < initial_pawn_morale  # Morale drops
    print(f"pawn.emotional_state.confidence: {pawn.emotional_state.confidence}")
    print(f"pawn.emotional_state.morale: {pawn.emotional_state.morale}")
    
    # Verify team psychological impact from threat
    assert default_moderator.psychological_state.morale < initial_team_morale  # Team morale drops
    assert default_moderator.psychological_state.cohesion > initial_team_cohesion  # Team unites against threat
    
    # Record initial states before trauma
    pre_trauma_team_morale = default_moderator.psychological_state.morale
    pre_trauma_team_coordination = default_moderator.psychological_state.coordination
    pre_trauma_pawn_confidence = pawn.emotional_state.confidence
    print(f"pre_trauma_pawn_confidence: {pre_trauma_pawn_confidence}")
    
    # Record a capture
    mediator.register_opponent_action(
        position=starting_position,
        move="f6e4",  # Black captures our pawn
        affected_pieces=["Pe2"],  # Still reference by starting position
        interaction_type=InteractionType.TRAUMA,
        turn=2
    )
    
    # Verify trauma was recorded
    last_interaction = mediator.relationship_network.recent_interactions[-1]
    assert last_interaction.type == InteractionType.TRAUMA
    assert last_interaction.impact < -0.3  # Major negative impact
    
    # Verify individual piece impact from trauma
    assert pawn.emotional_state.confidence < pre_trauma_pawn_confidence  # Confidence drops further
    assert pawn.emotional_state.morale < 0.2  # Morale severely impacted
    
    # Verify team psychological impact from trauma
    assert default_moderator.psychological_state.morale < pre_trauma_team_morale  # Team morale drops further
    assert default_moderator.psychological_state.coordination < pre_trauma_team_coordination  # Team coordination suffers
    assert default_moderator.psychological_state.leadership < 0.55  # Leadership is questioned

def test_debate_consensus_effects(default_moderator, starting_position):
    """Test how debate consensus affects team psychology"""
    moves = ["e2e4"]  # Simple position with clear best move
    debate = default_moderator.conduct_debate(starting_position, moves)
    
    # If there's strong consensus, team psychology should improve
    if debate.has_consensus:
        psych_state = default_moderator.psychological_state
        assert psych_state.cohesion > 0.5
        assert psych_state.morale > 0.5

def test_piece_personality_influence(default_moderator, starting_position):
    """Test how piece personalities influence their proposals"""
    moves = ["g1f3"]  # Knight move
    debate = default_moderator.conduct_debate(starting_position, moves)
    
    # Find knight's proposal
    knight_proposal = next(
        p for p in debate.proposals 
        if p.move == "g1f3"
    )
    
    # Knight's quixotic nature should show in argument
    assert any(
        phrase in knight_proposal.argument.lower()
        for phrase in ["quest", "adventure", "noble", "challenge"]
    )

def test_interaction_recording(default_moderator):
    """Test recording and impact of piece interactions"""
    # Setup a position where knight can save queen
    sacrifice_position = Position(
        fen="r1bkqb1r/pppp1ppp/2n5/8/2B5/5N2/PPPP1PPP/RNBQK2R w KQ - 0 4",
        move_history=["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]
    )
    
    # Knight moves to block check
    moves = ["f3e5"]  # Sacrificial move
    debate = default_moderator.conduct_debate(sacrifice_position, moves)
    
    # Select sacrificial move
    default_moderator.select_winning_proposal(debate, 0)
    
    # Verify sacrifice was recorded
    interactions = default_moderator.interaction_mediator.relationship_network.recent_interactions
    sacrifice = next(
        (i for i in interactions if i.type == InteractionType.SACRIFICE),
        None
    )
    
    assert sacrifice is not None
    assert sacrifice.piece1 == "N"  # Knight
    assert sacrifice.impact > 0  # Positive impact on relationships

def test_emotional_state_influence(default_moderator, starting_position):
    """Test how emotional state affects move evaluation"""
    king_side_knight = default_moderator.pieces['Ng1']
    queen_side_knight = default_moderator.pieces['Nb1']
    
    # Simulate confident emotional state
    king_side_knight.emotional_state = EmotionalState(
        confidence=0.8,
        aggression=0.7,
        morale=0.6,
        trust=0.5
    )
    queen_side_knight.emotional_state = EmotionalState(
        confidence=0.8,
        aggression=0.7,
        morale=0.6,
        trust=0.5
    )
    
    moves = ["g1f3", "b1c3"]  # Knight moves
    debate = default_moderator.conduct_debate(starting_position, moves)
    
    # High confidence should lead to more aggressive evaluation
    knight_proposals = [p for p in debate.proposals if p.move in moves]
    assert any(p.score > 0 for p in knight_proposals)  # At least one positive score
    
    # Arguments should reflect confidence
    assert any(
        "daring" in p.argument.lower() or
        "noble" in p.argument.lower()
        for p in knight_proposals
    ) 