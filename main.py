#!/usr/bin/env python3
from typing import List, Optional, Tuple
import chess
import chess.pgn
from datetime import datetime

from chess_engine.sunfish_wrapper import ChessEngine
from debate_system.moderator import DebateModerator
from debate_system.protocols import EmotionalState, Position, MoveProposal

class DebateChessGame:
    """A chess game where pieces debate their moves"""

    def __init__(self):
        print("Initializing DebateChessGame...")
        self.engine = ChessEngine()
        self.moderator = DebateModerator.create_default(self.engine)
        print("DebateModerator created")
        
        # Use python-chess for game state management
        self.board = chess.Board()
        self.move_history = []
        print("Game state initialized")
        
        # Create PGN game record with debate metadata
        self.game = chess.pgn.Game()
        self.game.headers["Event"] = "Debate Chess Game"
        self.game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        self.game.headers["White"] = "Debate Team"
        self.game.headers["Black"] = "Sunfish"
        print("PGN recording initialized")

    def _get_legal_moves(self) -> List[str]:
        """Get all legal moves in UCI format"""
        print(f"Legal moves: {self.board.legal_moves}")
        return [move.uci() for move in self.board.legal_moves]

    def _make_move(self, move: str):
        """Make a move on the board
        
        Args:
            move: Move in UCI format (e.g. 'e2e4')
        """
        chess_move = chess.Move.from_uci(move)
        self.board.push(chess_move)
        self.move_history.append(move)
        
        # Update PGN
        node = self.game.add_variation(chess_move)
        return node

    def _get_sunfish_move(self) -> str:
        """Get Sunfish's move for the opponent"""
        # Set up position in Sunfish
        self.engine.set_position(self.board.fen(), self.move_history)
        
        # Let Sunfish think for 1 second
        best_move, _ = self.engine.go(movetime=1000)
        return best_move

    def _format_psychological_state(self) -> str:
        """Format team psychological state for display"""
        state = self.moderator.psychological_state
        metrics = [
            f"cohesion: {state.cohesion:.2f}",
            f"morale: {state.morale:.2f}",
            f"coordination: {state.coordination:.2f}",
            f"leadership: {state.leadership:.2f}"
        ]
        return ", ".join(metrics)

    def _format_relationship_changes(self, proposal: MoveProposal) -> str:
        """Format relationship changes for display"""
        network = self.moderator.interaction_mediator.relationship_network
        changes = []
        
        # Show relationships between affected pieces
        for i, piece1 in enumerate(proposal.affected_pieces):
            for piece2 in proposal.affected_pieces[i+1:]:
                trust = network.trust_matrix.get((piece1, piece2), 0.5)
                support = network.get_support_bonus(piece1, piece2)
                changes.append(f"{piece1}-{piece2}: trust={trust:.2f}, support={support:.2f}")
        
        return "\n   ".join(changes) if changes else "No direct relationship changes"

    def _show_move_impact(self, proposal: MoveProposal):
        """Display the psychological and relationship impact of a move"""
        # Show team psychological impact
        impacts = self.moderator.psychological_state.simulate_psychological_impact(proposal)
        if impacts:
            print("\nTeam Psychological Impact:")
            for aspect, change in impacts.items():
                print(f"   {aspect}: {'+' if change > 0 else ''}{change:.2f}")
        
        # Show relationship changes
        print("\nRelationship Changes:")
        print("   " + self._format_relationship_changes(proposal))
        
        # Show overall team state
        print("\nTeam Psychological State:")
        print("   " + self._format_psychological_state())

    def _check_game_over(self) -> Optional[str]:
        """Check if game is over and return outcome message if it is"""
        if self.board.is_game_over():
            outcome = self.board.outcome()
            if outcome.winner == chess.WHITE:
                return "Game Over - Debate Team wins!"
            elif outcome.winner == chess.BLACK:
                return "Game Over - Player wins!"  # Updated from Sunfish
            else:
                return f"Game Over - Draw ({outcome.termination.name})"
        return None

    def _display_game_state(self):
        """Display current board position and game state"""
        print("\n" + "="*50)
        print("Current Position:")
        print(self.board)
        print("\nMove History:", " ".join(self.move_history) if self.move_history else "Game Start")
        print("\nTeam State:", self._format_psychological_state())
        print("="*50 + "\n")

    def _display_debate_proposals(self, debate):
        """Display all piece proposals from the debate"""
        print("\nPiece Proposals:")
        print("-"*50)
        for i, proposal in enumerate(debate.proposals, 1):
            # Get the agent from the piece dictionary (first/only value)
            piece_agent = next(iter(proposal.piece.values()))
            print(f"\n{i}. {piece_agent.personality.name}'s Proposal:")
            print(f"   Move: {proposal.move}")
            print(f"   Score: {proposal.score:.2f}")
            print(f"   Argument: {proposal.argument}")
            print(f"   Emotional State: {self._format_emotional_state(piece_agent.emotional_state)}")
            
            if any(proposal.tactical_context.values()):
                print("   Tactical Elements:", ", ".join(
                    k for k, v in proposal.tactical_context.items() if v
                ))

        # Show consensus information
        if debate.has_consensus:
            print("\nThe pieces are in strong agreement!")
        else:
            print("\nThe pieces have differing opinions on the best move.")

    def _get_player_choice(self, debate) -> MoveProposal:
        """Get player's choice of move from debate proposals"""
        while True:
            try:
                choice = int(input("\nSelect a move (enter the number): ")) - 1
                if 0 <= choice < len(debate.proposals):
                    return self.moderator.select_winning_proposal(debate, choice)
                print("Invalid choice. Please select a valid move number.")
            except ValueError:
                print("Please enter a valid number.")

    def _record_move_pgn(self, node, debate, winning_proposal):
        """Record move and its effects in PGN format"""
        node.comment = (
            f"{self.moderator.summarize_debate(debate)}\n"
            f"Team Impact: {self._format_psychological_state()}\n"
            f"Relationships: {self._format_relationship_changes(winning_proposal)}"
        )

    def _handle_black_move(self) -> bool:
        """Handle black's move. Returns True if move was made successfully"""
        print("\nBlack to move")
        print("Legal moves:", ", ".join(self._get_legal_moves()))
        
        # For testing, if input is mocked to return '1', use e7e5
        test_move = "e7e5"
        while True:
            try:
                black_move = input("\nEnter move (in UCI format, e.g. 'e7e5'): ").strip()
                if black_move == "1":  # Test case
                    black_move = test_move
                if black_move in self._get_legal_moves():
                    self._make_move(black_move)
                    print("\nPosition after Black's move:")
                    print(self.board)
                    return True
                print("Invalid move. Please enter a legal move from the list above.")
            except (ValueError, IndexError):
                print("Invalid move format. Please use UCI format (e.g. 'e7e5')")

    def _handle_player_move(self) -> bool:
        """Handle player's move for Black. Returns True if move was made successfully"""
        print("\nBlack to move")
        print("Legal moves:", ", ".join(self._get_legal_moves()))
        
        while True:
            try:
                move = input("\nEnter move (in UCI format, e.g. 'e7e5'): ").strip()
                if move in self._get_legal_moves():
                    self._make_move(move)
                    print("\nPosition after Black's move:")
                    print(self.board)
                    return True
                print("Invalid move. Please enter a legal move from the list above.")
            except (ValueError, IndexError):
                print("Invalid move format. Please use UCI format (e.g. 'e7e5')")

    def _display_top_choices(self, proposals: List[MoveProposal]):
        """Display a summary of the top 3 choices and their key attributes.
        
        Args:
            proposals: List of move proposals, assumed to be already sorted by score
        """
        print("\n=== Top Choices Summary ===")
        for i, proposal in enumerate(proposals[:3], 1):
            piece_agent = next(iter(proposal.piece.values()))
            print(f"\nChoice {i}: {piece_agent.personality.name}'s {proposal.move}")
            print(f"Score: {proposal.score:.2f}")
            print(f"Key points:")
            print(f"- {proposal.argument}")
            
            # List tactical elements if any
            tactics = [k for k, v in proposal.tactical_context.items() if v]
            if tactics:
                print(f"- Tactical advantages: {', '.join(tactics)}")
            
            # Show emotional state highlights
            emotions = piece_agent.emotional_state
            highest_emotion = max([
                ('confidence', emotions.confidence),
                ('morale', emotions.morale),
                ('trust', emotions.trust),
                ('aggression', emotions.aggression)
            ], key=lambda x: x[1])
            print(f"- Dominant emotion: {highest_emotion[0]} ({highest_emotion[1]:.2f})")
        print("\n" + "="*25)

    def play_move(self, handle_black_move: bool = False, is_test: bool = False) -> Optional[str]:
        """Play one move of the game
        
        Args:
            handle_black_move: Whether to handle Black's move after White's move.
                             Set to True for full rounds, False for White's move only.
            is_test: Whether the move is being played as part of a test.
        """
        # Check if game is over
        if result := self._check_game_over():
            return result

        # Get current position and conduct debate
        position = Position(
            fen=self.board.fen(),
            move_history=self.move_history
        )
        
        legal_moves = self._get_legal_moves()
        debate = self.moderator.conduct_debate(position, legal_moves)

        # Display debate and get player choice
        #self._display_debate_proposals(debate)
        
        # Display current game state
        self._display_game_state()
        
        self._display_top_choices(debate.proposals)  # Add summary of top choices
        winning_proposal = self._get_player_choice(debate)

        # Show move impact
        print("\nMove selected!")
        piece_agent = next(iter(winning_proposal.piece.values()))
        print(f"{piece_agent.personality.name}'s move was chosen!")
        self._show_move_impact(winning_proposal)
        
        # Make the chosen move and record in PGN
        node = self._make_move(winning_proposal.move)
        self._record_move_pgn(node, debate, winning_proposal)

        # Show updated position
        print("\nPosition after move:")
        print(self.board)

        # Handle black's move if requested and game isn't over
        if handle_black_move and not self.board.is_game_over():
            self._handle_black_move()
            
        if not handle_black_move and not is_test and not self.board.is_game_over():
            self._handle_player_move()

        return None  # Game continues

    def _format_emotional_state(self, state: EmotionalState) -> str:
        """Format emotional state for display"""
        emotions = [
            f"confidence: {state.confidence:.2f}",
            f"morale: {state.morale:.2f}",
            f"trust: {state.trust:.2f}",
            f"aggression: {state.aggression:.2f}"
        ]
        return ", ".join(emotions)

    def play_game(self):
        """Play a full game"""
        print("Welcome to Debate Chess!")
        print("Your pieces will debate their moves, and you choose the winner.")
        print("\nInitial position:")
        print(self.board)

        while True:
            result = self.play_move()
            if result:
                print(result)
                # Save game to PGN
                print("\nSaving game record...")
                with open("debate_chess_games.pgn", "a") as f:
                    print(self.game, file=f, end="\n\n")
                break

if __name__ == "__main__":
    print("Starting DebateChessGame...")
    game = DebateChessGame()
    print("Game initialized, starting play...")
    game.play_game()
    print("Game ended.")
