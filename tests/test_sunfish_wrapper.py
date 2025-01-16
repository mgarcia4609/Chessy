import pytest
import chess
from chess_engine.sunfish_wrapper import ChessEngine, EngineAnalysis

@pytest.fixture
def engine():
    """Create a fresh engine instance for each test"""
    return ChessEngine()

def test_engine_creation(engine):
    """Test that engine is created and initialized properly"""
    assert engine._board is not None
    assert isinstance(engine._board, chess.Board)

def test_set_position(engine):
    """Test setting different positions"""
    # Test starting position
    engine.set_position()
    assert engine._board.fen().split()[0] == chess.STARTING_FEN.split()[0]
    
    # Test custom FEN
    test_fen = "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2"
    engine.set_position(test_fen)
    assert engine._board.fen().split()[0] == test_fen.split()[0]
    
    # Test position after moves
    engine.set_position(moves=["e2e4", "c7c5"])
    assert engine._board.fen().split()[0] == test_fen.split()[0]

def test_evaluation(engine):
    """Test the position evaluation function"""
    # Starting position should be equal
    analysis = engine.evaluate_position()
    assert isinstance(analysis, EngineAnalysis)
    assert abs(analysis.score) < 1.0             # Small imbalance due to mobility/center control is normal
    assert abs(analysis.material_balance) < 0.1  # Material should be exactly equal
    assert analysis.center_control == 0          # White has slight center advantage due to first move
    
    # Test material advantage
    engine.set_position(fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1")
    analysis = engine.evaluate_position()
    assert analysis.material_balance == -6.5     # Missing knight (-3.2) and bishop (-3.3)
    
    # Test central control and mobility
    engine.set_position(fen="rnbqkbnr/ppp2ppp/8/3pp3/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 1")
    analysis = engine.evaluate_position()
    assert abs(analysis.material_balance) == 0  # Equal material
    assert abs(analysis.center_control) == 0    # Both control center
    assert analysis.positional_score == 0       # Pawn structure affects position
    
    # Test mobility and piece placement
    engine.set_position(fen="r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
    analysis = engine.evaluate_position()
    assert abs(analysis.mobility_score) < 0.2   # Position is balanced in development
    assert abs(analysis.positional_score) < 0.2 # Development is roughly equal
    
    # Test king safety
    engine.set_position(fen="rnbqk2r/pppp1ppp/5n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
    early_analysis = engine.evaluate_position()
    engine.set_position(fen="rnbqk2r/pppp1ppp/5n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 0 1")
    castle_analysis = engine.evaluate_position()
    assert castle_analysis.king_safety > early_analysis.king_safety
    
    # Test advanced pawns and bishop pair
    engine.set_position(fen="4k3/2P5/8/8/2B1B3/8/8/4K3 w - - 0 1")
    analysis = engine.evaluate_position()
    assert analysis.positional_score > 0      # Advanced pawn and bishop pair
    assert analysis.material_balance > 4      # Pawn + two bishops vs king
    
    # Test queen mobility in center vs corner
    engine.set_position(fen="8/8/8/8/3Q4/8/8/8 w - - 0 1")
    center_analysis = engine.evaluate_position()
    engine.set_position(fen="Q7/8/8/8/8/8/8/8 w - - 0 1")
    corner_analysis = engine.evaluate_position()
    assert center_analysis.mobility_score > corner_analysis.mobility_score  # Center queen has more moves

def test_board_utility_methods(engine):
    """Test the chess utility wrapper methods"""
    # Setup a position
    engine.set_position()
    
    g1_square = chess.parse_square("g1")
    attacked = engine.get_attacked_squares(g1_square) # A knight should attack 2 squares from the starting position
    assert isinstance(attacked, chess.SquareSet)
    assert len(attacked) == 2                         # f3 and h3 are attackable (e2 excluded as it has friendly pawn)
    assert chess.parse_square("f3") in attacked
    assert chess.parse_square("h3") in attacked
    assert chess.parse_square("e2") not in attacked   # Square with friendly pawn should be excluded
    
    # Test get_piece_at
    e2_square = chess.parse_square("e2")
    piece = engine.get_piece_at(e2_square)
    assert piece == chess.Piece.from_symbol("P")
    
    # Test get_piece_map
    piece_map = engine.get_piece_map()
    assert isinstance(piece_map, dict)
    assert len(piece_map) == 32
    
    # Test is_attacked_by with a more interesting position
    # Set up a position where e4 is attacked by a black pawn
    engine.set_position(fen="rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    e4_square = chess.parse_square("e4")
    assert engine.is_attacked_by(chess.BLACK, e4_square)
    
    # Test get_legal_moves in starting position
    engine.set_position()
    moves = engine.get_legal_moves()
    assert isinstance(moves, list)
    assert len(moves) == 20

def test_move_making(engine):
    """Test making moves on the board"""
    engine.set_position()
    
    # Make a move
    engine.make_move("e2e4")
    assert engine._board.piece_at(chess.E4) == chess.Piece.from_symbol("P")
    assert engine._board.piece_at(chess.E2) is None
    
    # Test move history
    engine.set_position(moves=["e2e4", "e7e5", "g1f3"])
    assert engine._board.piece_at(chess.F3) == chess.Piece.from_symbol("N")
    assert engine._board.fullmove_number == 2

def test_square_parsing(engine):
    """Test square parsing and coordinate functions"""
    e4 = engine.parse_square("e4")
    assert isinstance(e4, chess.Square)
    
    assert engine.square_file(e4) == chess.square_file(chess.E4)
    assert engine.square_rank(e4) == chess.square_rank(chess.E4)

def test_turn_tracking(engine):
    """Test turn tracking after moves"""
    engine.set_position()
    assert engine.get_turn() == chess.WHITE
    
    engine.make_move("e2e4")
    assert engine.get_turn() == chess.BLACK
    
    engine.make_move("e7e5")
    assert engine.get_turn() == chess.WHITE 

def test_get_potential_attacks(engine):
    """Test get_potential_attacks method"""
    g1_square = chess.parse_square("g1")
    attacked = engine.get_potential_attacks(g1_square)
    assert isinstance(attacked, chess.SquareSet)
    assert len(attacked) == 3                    # f3, h3, and e2 are potentially attackable
    assert chess.parse_square("f3") in attacked
    assert chess.parse_square("h3") in attacked
    assert chess.parse_square("e2") in attacked  # Square with friendly pawn