#!/usr/bin/env python3
import sys
from typing import List, Optional, Tuple
from sunfish import Position, Move, sunfish
from sunfish.tools import fancy
from debate_system.moderator import DebateModerator, DebateRound

class DebateChessGame:
    """A chess game where pieces debate their moves"""

    def __init__(self):
        self.moderator = DebateModerator.create_default()
        self.position = Position(sunfish.initial, 0, (True,True), (True,True), 0, 0)
        self.history: List[Tuple[Position, Move]] = []

    def _get_legal_moves(self) -> List[Move]:
        """Get all legal moves for the current position"""
        return list(self.position.gen_moves())

    def _make_move(self, move: Move):
        """Make a move on the board"""
        self.history.append((self.position, move))
        self.position = self.position.move(move)

    def _get_sunfish_move(self) -> Move:
        """Get Sunfish's move for the opponent"""
        move, score = sunfish.search(self.position)
        return move

    def play_move(self) -> Optional[str]:
        """Play one move of the game"""
        # Check if game is over
        legal_moves = self._get_legal_moves()
        if not legal_moves:
            return "Game Over - Checkmate!" if self.position.board.find('k') >= 0 else "Game Over - Stalemate!"

        debate = self.moderator.conduct_debate(self.position, legal_moves)

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
        self._make_move(winning_proposal.move)
        print(f"\n{winning_proposal.piece.name}'s move was chosen!")

        # Show the board
        print("\nCurrent position:")
        print(fancy.print_pos(self.position))

        # Make opponent's move
        if self._get_legal_moves():  # Check if game isn't over
            print("\nSunfish is thinking...")
            opponent_move = self._get_sunfish_move()
            self._make_move(opponent_move)
            print("\nSunfish's move:")
            print(fancy.print_pos(self.position))

        return None  # Game continues

    def play_game(self):
        """Play a full game"""
        print("Welcome to Debate Chess!")
        print("Your pieces will debate their moves, and you choose the winner.")
        print("\nInitial position:")
        print(fancy.print_pos(self.position))

        while True:
            result = self.play_move()
            if result:
                print(result)
                break

if __name__ == "__main__":
    game = DebateChessGame()
    game.play_game()
