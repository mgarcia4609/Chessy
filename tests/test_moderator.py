import pytest
import chess
from typing import Dict

from chess_engine.sunfish_wrapper import ChessEngine
from debate_system.moderator import DebateModerator, StandardDebate, DebateRound
from debate_system.protocols import (
    Position, MoveProposal, PersonalityConfig, EmotionalState,
    Interaction, InteractionType, GameMoment
)
from piece_agents.base_agent import ChessPieceAgent
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
    assert set(default_moderator.pieces.keys()) == {'N', 'B', 'R', 'Q', 'K', 'P'}
    
    # Verify piece personalities
    knight = default_moderator.pieces['N']
    assert "modern Don Quixote" in knight.personality.description
    assert knight.personality.tactical_weight == 1.2
    
    queen = default_moderator.pieces['Q']
    assert "drama queen" in queen.personality.description
    assert queen.personality.risk_tolerance > 0.5

def test_create_themed_moderator(aggressive_moderator):
    """Test creating moderator with themed personalities"""
    # Check personality modifications
    knight = aggressive_moderator.pieces['N']
    assert knight.personality.tactical_weight > 1.2  # More aggressive than default
    assert "aggressively" in knight.personality.description.lower()
    
    bishop = aggressive_moderator.pieces['B']
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
    
    # Verify it was recorded as cooperation
    last_interaction = mediator.relationship_network.recent_interactions[-1]
    assert last_interaction.type == "cooperation"
    assert last_interaction.impact > 0

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
        fen="r1bqkb1r/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
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
        (i for i in interactions if i.type == "sacrifice"),
        None
    )
    
    assert sacrifice is not None
    assert sacrifice.piece1 == "N"  # Knight
    assert sacrifice.impact > 0  # Positive impact on relationships

def test_emotional_state_influence(default_moderator, starting_position):
    """Test how emotional state affects move evaluation"""
    knight = default_moderator.pieces['N']
    
    # Simulate confident emotional state
    knight.emotional_state = EmotionalState(
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
        "confident" in p.argument.lower() or
        "bold" in p.argument.lower()
        for p in knight_proposals
    ) 