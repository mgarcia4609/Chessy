import pytest
import chess
from chess_engine.sunfish_wrapper import ChessEngine, EngineAnalysis
from piece_agents.base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import PersonalityConfig, Position

@pytest.fixture
def engine():
    """Create a fresh engine instance for each test"""
    return ChessEngine()

@pytest.fixture
def default_personality():
    """Create a default personality configuration"""
    return PersonalityConfig(
        name="default",
        description="Default personality",
        tactical_weight=0.5,
        positional_weight=0.5,
        risk_tolerance=0.5,
        options={}
    )

@pytest.fixture
def base_agent(engine, default_personality):
    """Create a base agent instance"""
    return ChessPieceAgent(engine=engine, personality=default_personality)

def test_tactical_opportunity_creation():
    """Test creating tactical opportunities"""
    opp = TacticalOpportunity(
        type="fork",
        target_squares={chess.E4, chess.F6},
        target_pieces=[chess.Piece.from_symbol("Q"), chess.Piece.from_symbol("N")],
        value=12.0,  # Queen (9) + Knight (3)
        description="A fork targeting Q and N",
        confidence=0.8
    )
    assert opp.type == "fork"
    assert len(opp.target_squares) == 2
    assert len(opp.target_pieces) == 2
    assert opp.value == 12.0
    assert isinstance(opp.confidence, float)

def test_find_knight_fork(base_agent):
    """Test detection of a basic knight fork position"""
    # Set up a position with a clear knight fork
    # White knight on d5 can fork black king on g8 and black rook on g6
    position = Position(
        fen="6k1/8/6r1/3N4/8/8/8/4K3 w - - 0 1",
        move_history=[]
    )
    
    # The move Ne7+ forks king and rook
    opportunities = base_agent._find_tactical_opportunities(position, "d5e7")
    
    assert len(opportunities) > 0
    fork = next((opp for opp in opportunities if opp.type == "fork"), None)
    assert fork is not None
    assert len(fork.target_squares) == 2  # Should attack exactly 2 pieces
    assert len(fork.target_pieces) == 2
    
    # Verify we found the right pieces
    piece_symbols = {p.symbol() for p in fork.target_pieces}
    assert piece_symbols == {'k', 'r'}  # Should fork king and rook
    assert fork.value == 5  # Value of rook (king has no material value)

def test_calculate_weighted_score(base_agent):
    """Test score calculation with personality weights"""
    # Create a mock analysis with known components
    analysis = EngineAnalysis(
        score=1.0,               # Overall score (not directly used anymore)
        material_balance=1.0,    # Winning by a pawn
        mobility_score=0.2,      # Slight mobility advantage
        positional_score=0.3,    # Minor positional advantage
        center_control=0.2,      # Some center control
        king_safety=0.1,         # Slightly safer king
        depth=3
    )
    
    # Test with default personality (0.5 weights)
    score = base_agent._calculate_weighted_score(analysis)
    expected_tactical = (1.0 + 0.2) * 0.5                    # (material + mobility) * tactical_weight
    expected_positional = (0.3 + 0.2 + 0.1) * 0.5            # (position + center + safety) * positional_weight
    expected_base = expected_tactical + expected_positional
    expected_score = expected_base * 1.1                     # risk_factor for winning position with 0.5 tolerance
    assert abs(score - expected_score) < 0.1
    
    # Test with tactical personality
    tactical_personality = PersonalityConfig(
        name="tactical",
        description="Tactical personality",
        tactical_weight=0.8,
        positional_weight=0.2,
        risk_tolerance=0.7,
        options={}
    )
    tactical_agent = ChessPieceAgent(engine=base_agent.engine, personality=tactical_personality)
    tactical_score = tactical_agent._calculate_weighted_score(analysis)
    assert tactical_score > score  # Should value tactical advantages more
    
    # Test with positional personality
    positional_personality = PersonalityConfig(
        name="positional",
        description="Positional personality",
        tactical_weight=0.2,
        positional_weight=0.8,
        risk_tolerance=0.3,
        options={}
    )
    positional_agent = ChessPieceAgent(engine=base_agent.engine, personality=positional_personality)
    positional_score = positional_agent._calculate_weighted_score(analysis)
    assert positional_score < tactical_score  # Should be more conservative 

def test_piece_value_calculation(base_agent):
    """Test piece value calculations"""
    queen = chess.Piece.from_symbol("Q")
    knight = chess.Piece.from_symbol("N")
    pawn = chess.Piece.from_symbol("P")
    
    assert base_agent._get_piece_value(queen) == 9
    assert base_agent._get_piece_value(knight) == 3
    assert base_agent._get_piece_value(pawn) == 1

def test_discovered_attack_detection(base_agent):
    """Test detection of discovered attacks"""
    # Position where moving a knight reveals a bishop attack
    position = Position(
        fen="8/6q1/8/8/3N4/2B5/8/4Q3 w - - 0 1",
        move_history=[]
    )
    
    opportunities = base_agent._find_tactical_opportunities(position, "d4e6")
    
    discovered = next((opp for opp in opportunities if opp.type == "discovered_attack"), None)
    assert discovered is not None
    assert len(discovered.target_squares) > 0
    assert discovered.confidence > 0

def test_tactic_confidence_calculation(base_agent):
    """Test confidence calculations for tactical opportunities"""
    # Set up a position where a piece is attacking but also under attack
    position = Position(
        fen="4k3/8/8/3N4/8/8/8/4K3 w - - 0 1",
        move_history=[]
    )
    
    knight_square = chess.parse_square("d5")
    target_squares = {chess.parse_square("e7"), chess.parse_square("c7")}
    
    confidence = base_agent._calculate_tactic_confidence(knight_square, target_squares)
    assert 0 <= confidence <= 1
