#!/usr/bin/env python3
from typing import List, Optional, Tuple
import chess
import chess.pgn
from datetime import datetime

from chess_engine.sunfish_wrapper import SunfishEngine
from debate_system.moderator import DebateModerator
from debate_system.protocols import Position, MoveProposal

class DebateChessGame:
    """A chess game where pieces debate their moves"""

    def __init__(self):
        print("Initializing DebateChessGame...")
        self.engine = SunfishEngine.create_new()
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

    def play_move(self) -> Optional[str]:
        """Play one move of the game"""
        # Check if game is over
        if self.board.is_game_over():
            outcome = self.board.outcome()
            if outcome.winner == chess.WHITE:
                return "Game Over - Debate Team wins!"
            elif outcome.winner == chess.BLACK:
                return "Game Over - Sunfish wins!"
            else:
                return f"Game Over - Draw ({outcome.termination.name})"

        # Get current position
        position = Position(
            fen=self.board.fen(),
            move_history=self.move_history
        )
        
        # Get legal moves and conduct debate
        legal_moves = self._get_legal_moves()
        debate = self.moderator.conduct_debate(position, legal_moves)

        # Display the debate
        print("\nPieces are debating their moves...")
        print(self.moderator.summarize_debate(debate))

        # Get player choice
        while True:
            try:
                choice = int(input("\nSelect a move (enter the number): ")) - 1
                winning_proposal = self.moderator.select_winning_proposal(debate, choice)
                break
            except (ValueError, IndexError):
                print("Invalid choice. Please try again.")

        # Make the chosen move
        node = self._make_move(winning_proposal.move)
        print(f"\n{winning_proposal.piece.name}'s move was chosen!")
        
        # Add debate summary to PGN comments
        node.comment = self.moderator.summarize_debate(debate)

        # Show the board
        print("\nCurrent position:")
        print(self.board)

        # Make opponent's move if game isn't over
        if not self.board.is_game_over():
            print("\nSunfish is thinking...")
            opponent_move = self._get_sunfish_move()
            self._make_move(opponent_move)
            print("\nSunfish's move:")
            print(self.board)

        return None  # Game continues

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
