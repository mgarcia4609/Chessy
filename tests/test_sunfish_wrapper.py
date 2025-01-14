import pytest
import chess
print("chess imports done")
from chess_engine.sunfish_wrapper import SunfishEngine, EngineAnalysis, ChessConstants
print("sunfish wrapper imported")

@pytest.fixture
def engine():
    """Create a fresh engine instance for each test"""
    engine = SunfishEngine.create_new()
    yield engine
    engine.quit()  # Cleanup after test

def test_engine_creation(engine):
    """Test that engine process is created and initialized properly"""
    assert engine.process is not None
    assert engine._is_ready is True
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

def test_go_command(engine):
    """Test the go command returns valid moves and analysis"""
    best_move, analyses = engine.go(movetime=100)  # 100ms should be enough for testing
    
    # Verify best_move format
    assert isinstance(best_move, str)
    assert len(best_move) >= 4  # Minimum move length e.g., "e2e4"
    
    # Verify analyses
    assert isinstance(analyses, list)
    if analyses:  # Some engines might not provide analysis info
        analysis = analyses[0]
        assert isinstance(analysis, EngineAnalysis)
        assert analysis.depth >= 1
        assert isinstance(analysis.score, int)
        assert isinstance(analysis.pv, list)
        assert isinstance(analysis.nodes, int)
        assert isinstance(analysis.time_ms, int)
        assert isinstance(analysis.nps, int)

def test_board_utility_methods(engine):
    """Test the chess utility wrapper methods"""
    # Setup a position
    engine.set_position()
    
    # Test get_attacked_squares
    e2_square = chess.parse_square("e2")
    attacked = engine.get_attacked_squares(e2_square)
    assert isinstance(attacked, set)
    
    # Test get_piece_at
    piece = engine.get_piece_at(e2_square)
    assert piece == chess.Piece.from_symbol("P")
    
    # Test get_piece_map
    piece_map = engine.get_piece_map()
    assert isinstance(piece_map, dict)
    assert len(piece_map) == 32  # Starting position has 32 pieces
    
    # Test is_attacked_by
    assert not engine.is_attacked_by(chess.BLACK, e2_square)
    
    # Test get_legal_moves
    moves = engine.get_legal_moves()
    assert isinstance(moves, list)
    assert len(moves) == 20  # Starting position has 20 legal moves

def test_process_cleanup(engine):
    """Test that the engine process is properly cleaned up"""
    process = engine.process
    engine.quit()
    
    # Process should have terminated
    assert process.poll() is not None

def test_invalid_position():
    """Test handling of invalid positions"""
    engine = SunfishEngine.create_new()
    with pytest.raises(Exception):  # Should raise some kind of exception
        engine.set_position("invalid fen")
    engine.quit()

def test_multiple_moves(engine):
    """Test making multiple moves and analyzing positions"""
    # Make a series of moves
    moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
    engine.set_position(moves=moves)
    
    # Verify position is correct
    expected_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    assert engine._board.fen().split()[0] == expected_fen.split()[0]
    
    # Get analysis of position
    best_move, analyses = engine.go(movetime=100)
    assert best_move is not None
    assert isinstance(best_move, str)

def test_concurrent_analysis():
    """Test that multiple engine instances don't interfere"""
    engine1 = SunfishEngine.create_new()
    engine2 = SunfishEngine.create_new()
    
    # Set different positions
    engine1.set_position(moves=["e2e4"])
    engine2.set_position(moves=["d2d4"])
    
    # Get analyses
    move1, _ = engine1.go(movetime=100)
    move2, _ = engine2.go(movetime=100)
    
    assert move1 != move2  # Different positions should yield different moves
    
    engine1.quit()
    engine2.quit() 