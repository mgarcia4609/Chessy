import pytest
import chess
from debate_system.protocols import EmotionalState, Position, MoveProposal
from main import DebateChessGame

@pytest.fixture
def game():
    return DebateChessGame()

@pytest.fixture
def game_with_moves(game):
    # Make a few moves to test mid-game scenarios
    game.board.push_uci("e2e4")  # 1.e4
    game.board.push_uci("e7e5")  # 1...e5
    game.move_history = ["e2e4", "e7e5"]
    return game

def test_check_game_over_initial(game):
    assert game._check_game_over() is None

def test_check_game_over_checkmate():
    # Fool's mate position
    game = DebateChessGame()
    moves = ["f2f3", "e7e5", "g2g4", "d8h4"]
    for move in moves:
        game.board.push_uci(move)
    
    result = game._check_game_over()
    assert result == "Game Over - Player wins!"

def test_get_legal_moves(game_with_moves):
    legal_moves = game_with_moves._get_legal_moves()
    # After 1.e4 e5, white should have 28 legal moves
    assert len(legal_moves) == 29
    assert "g1f3" in legal_moves  # Knight to f3 should be possible

def test_format_psychological_state(game):
    # Test that all metrics are included and formatted correctly
    state_str = game._format_psychological_state()
    assert "cohesion:" in state_str
    assert "morale:" in state_str
    assert "coordination:" in state_str
    assert "leadership:" in state_str
    
    # Test that values are formatted to 2 decimal places
    for metric in state_str.split(", "):
        value = float(metric.split(": ")[1])
        assert 0 <= value <= 1

def test_format_emotional_state():
    game = DebateChessGame()
    state = EmotionalState(
        confidence=0.8,
        morale=0.6,
        trust=0.7,
        aggression=0.4
    )
    result = game._format_emotional_state(state)
    assert result == "confidence: 0.80, morale: 0.60, trust: 0.70, aggression: 0.40"

def test_display_game_state(game_with_moves, capsys):
    game_with_moves._display_game_state()
    captured = capsys.readouterr()
    
    # Check that key elements are displayed
    assert "Current Position:" in captured.out
    assert "Move History: e2e4 e7e5" in captured.out
    assert "Team State:" in captured.out

def test_handle_black_move_valid(game, monkeypatch):
    # Mock input to simulate valid move entry
    monkeypatch.setattr('builtins.input', lambda _: 'e7e5')
    
    # Make an opening move to enable e7e5
    game.board.push_uci("e2e4")
    
    assert game._handle_black_move() is True
    assert game.board.move_stack[-1].uci() == "e7e5"

def test_handle_black_move_invalid_then_valid(game, monkeypatch):
    # Mock input to simulate invalid move then valid move
    inputs = iter(['invalid', 'e7e5'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    # Make an opening move to enable e7e5
    game.board.push_uci("e2e4")
    
    assert game._handle_black_move() is True
    assert game.board.move_stack[-1].uci() == "e7e5" 

def test_full_debate_round_integration(game, monkeypatch):
    """Test a complete debate round including proposal, selection, and impact"""
    # Mock player input to select first proposal
    monkeypatch.setattr('builtins.input', lambda _: '1')
    
    # Get initial psychological state
    initial_psych = game.moderator.psychological_state.cohesion
    
    # Conduct debate and select move
    position = Position(
        fen=game.board.fen(),
        move_history=[]
    )
    
    # Run through white's move process only
    result = game.play_move(handle_black_move=False)
    
    # Verify debate had impact
    assert game.moderator.psychological_state.cohesion != initial_psych
    assert len(game.move_history) == 1  # One move should be recorded
    assert game.board.move_stack  # Board should have the move

def test_pgn_recording(game, monkeypatch):
    """Test that PGN recording includes debate summaries"""
    # Mock player inputs for two moves
    inputs = iter(['1', 'e7e5'])  # First proposal for white, e5 for black
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    # Play one full round
    game.play_move()
    
    # Check PGN recording
    last_node = game.game.end()
    assert last_node.comment  # Should have debate summary
    assert "Team Impact:" in last_node.comment
    assert "Relationships:" in last_node.comment

def test_relationship_changes_after_move(game, monkeypatch):
    """Test that relationships update after move selection"""
    # Mock player input
    monkeypatch.setattr('builtins.input', lambda _: '1')
    
    # Get initial relationship state
    network = game.moderator.interaction_mediator.relationship_network
    initial_interactions = len(network.recent_interactions)
    
    # Make a move
    game.play_move()
    
    # Verify relationships were updated
    assert len(network.recent_interactions) > initial_interactions

def test_game_state_transitions(game, monkeypatch):
    """Test game state transitions between white and black moves"""
    # Setup inputs for a full round
    inputs = iter(['1', 'e7e5'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    # Initial state
    assert game.board.turn == chess.WHITE
    
    # Play move and verify transitions
    game.play_move(handle_black_move=True)
    
    # After full round
    assert len(game.move_history) == 2  # Both moves recorded
    assert game.board.turn == chess.WHITE  # Back to white
    assert game.board.fullmove_number == 2  # Move number increased 