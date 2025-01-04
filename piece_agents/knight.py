"""A knight that loves to create chaos and find tactical opportunities"""
from dataclasses import dataclass
from typing import List, Set, Dict, Optional
import chess

from .base_agent import ChessPieceAgent
from debate_system.protocols import Position, EngineAnalysis, EmotionalState
from chess_engine.sunfish_wrapper import SunfishEngine

@dataclass
class TacticalOpportunity:
    """Represents a tactical opportunity like a fork or discovered attack"""
    type: str                          # 'fork', 'discovered_attack', etc.
    target_squares: Set[chess.Square]  # Squares being attacked
    target_pieces: List[chess.Piece]   # Pieces being attacked
    value: float                       # Material value of the opportunity
    description: str                   # Natural language description
    confidence: float                  # How certain we are about this opportunity (0-1)

class KnightAgent(ChessPieceAgent):
    """A knight that loves to create chaos and find tactical opportunities"""
    
    def __init__(self, engine: SunfishEngine, personality, emotional_state: Optional[EmotionalState] = None):
        super().__init__(engine, personality)
        self.emotional_state = emotional_state or EmotionalState()
        self._tactical_cache: Dict[str, List[TacticalOpportunity]] = {}
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include knight-specific weights"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Knights get extra bonus for depth (representing complex tactics)
        depth_bonus = analysis.depth * 0.1 * self.emotional_state.confidence
        
        # Bonus for number of legal moves (knight mobility)
        mobility_bonus = len(analysis.legal_moves) * 0.05 * self.emotional_state.risk_modifier
        
        return base_score + depth_bonus + mobility_bonus
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities like forks and discovered attacks"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        board = chess.Board(position.fen)
        opportunities = []
        
        # Make the move on a copy of the board
        board.push(chess.Move.from_uci(move))
        
        # Calculate attacked squares after the move
        knight_square = chess.parse_square(move[2:4])
        attacked_squares = self._get_knight_attacked_squares(board, knight_square)
        
        # Look for forks
        fork_opportunities = self._find_forks(board, knight_square, attacked_squares)
        opportunities.extend(fork_opportunities)
        
        # Look for discovered attacks
        discovered_opportunities = self._find_discovered_attacks(board, knight_square, position)
        opportunities.extend(discovered_opportunities)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _get_knight_attacked_squares(self, board: chess.Board, square: chess.Square) -> Set[chess.Square]:
        """Get all squares attacked by knight at given square"""
        return {s for s in chess.SQUARES if chess.square_distance(square, s) == 2}
        
    def _find_forks(self, board: chess.Board, knight_square: chess.Square, 
                    attacked_squares: Set[chess.Square]) -> List[TacticalOpportunity]:
        """Find fork opportunities where knight attacks multiple valuable pieces"""
        opportunities = []
        attacked_pieces = []
        
        # Collect valuable pieces being attacked
        for square in attacked_squares:
            piece = board.piece_at(square)
            if piece and piece.color != board.turn:
                attacked_pieces.append((square, piece))
                
        # Look for valuable combinations (2 or more pieces)
        if len(attacked_pieces) >= 2:
            target_squares = {s for s, _ in attacked_pieces}
            target_pieces = [p for _, p in attacked_pieces]
            
            # Calculate fork value based on piece values
            value = sum(self._get_piece_value(p) for p in target_pieces)
            
            # Generate description
            desc = self._generate_fork_description(target_pieces, value)
            
            # Confidence based on protection
            confidence = self._calculate_tactic_confidence(board, knight_square, target_squares)
            
            opportunities.append(TacticalOpportunity(
                type='fork',
                target_squares=target_squares,
                target_pieces=target_pieces,
                value=value,
                description=desc,
                confidence=confidence
            ))
            
        return opportunities
        
    def _find_discovered_attacks(self, board: chess.Board, knight_square: chess.Square,
                               position: Position) -> List[TacticalOpportunity]:
        """Find opportunities where knight move reveals attack from another piece"""
        opportunities = []
        
        # Get the original position before the knight moved
        original_board = chess.Board(position.fen)
        
        # Find our attacking pieces (excluding the knight that moved)
        our_pieces = {
            square: piece for square, piece in original_board.piece_map().items()
            if piece.color == original_board.turn and square != knight_square
        }
        
        # Find enemy valuable pieces
        enemy_pieces = {
            square: piece for square, piece in board.piece_map().items()
            if piece.color != board.turn
        }
        
        # Check each of our pieces for potential discovered attacks
        for our_square, our_piece in our_pieces.items():
            # Skip if piece is not a sliding piece (bishop, rook, queen)
            if our_piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                continue
                
            # Get attacked squares for this piece before and after knight move
            before_squares = self._get_sliding_piece_squares(original_board, our_square)
            after_squares = self._get_sliding_piece_squares(board, our_square)
            
            # Find newly attacked squares
            new_squares = after_squares - before_squares
            
            # Check if any enemy pieces are in newly attacked squares
            for enemy_square, enemy_piece in enemy_pieces.items():
                if enemy_square in new_squares:
                    # We found a discovered attack!
                    value = self._get_piece_value(enemy_piece)
                    confidence = self._calculate_tactic_confidence(board, our_square, {enemy_square})
                    
                    desc = self._generate_discovered_attack_description(
                        our_piece, enemy_piece, value)
                    
                    opportunities.append(TacticalOpportunity(
                        type='discovered_attack',
                        target_squares={enemy_square},
                        target_pieces=[enemy_piece],
                        value=value,
                        description=desc,
                        confidence=confidence
                    ))
        
        return opportunities
        
    def _get_sliding_piece_squares(self, board: chess.Board, square: chess.Square) -> Set[chess.Square]:
        """Get all squares attacked by a sliding piece"""
        piece = board.piece_at(square)
        if not piece:
            return set()
            
        attacked = set()
        
        # Define movement directions based on piece type
        directions = []
        if piece.piece_type in [chess.ROOK, chess.QUEEN]:
            directions.extend([(0,1), (0,-1), (1,0), (-1,0)])
        if piece.piece_type in [chess.BISHOP, chess.QUEEN]:
            directions.extend([(1,1), (1,-1), (-1,1), (-1,-1)])
            
        # Look in each direction until we hit a piece or edge
        for dx, dy in directions:
            x = chess.square_file(square)
            y = chess.square_rank(square)
            
            while True:
                x += dx
                y += dy
                
                if not (0 <= x <= 7 and 0 <= y <= 7):
                    break
                    
                target = chess.square(x, y)
                attacked.add(target)
                
                if board.piece_at(target):
                    break
                    
        return attacked
        
    def _get_piece_value(self, piece: chess.Piece) -> float:
        """Get standard piece value with personality-based adjustments"""
        base_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # Kings aren't counted in material
        }
        
        value = base_values[piece.piece_type]
        
        # Adjust based on personality/emotional state
        if self.emotional_state.aggression > 0.7:
            # More aggressive knights value attacking pieces higher
            value *= 1.2
            
        return value
        
    def _calculate_tactic_confidence(self, board: chess.Board, 
                                   knight_square: chess.Square,
                                   target_squares: Set[chess.Square]) -> float:
        """Calculate how confident we are in a tactical opportunity"""
        # Base confidence from emotional state
        confidence = self.emotional_state.confidence
        
        # Reduce confidence if knight is under attack
        if board.is_attacked_by(not board.turn, knight_square):
            confidence *= 0.7
            
        # Reduce confidence if targets are well protected
        for square in target_squares:
            if board.is_attacked_by(not board.turn, square):
                confidence *= 0.8
                
        return min(1.0, max(0.1, confidence))
        
    def _generate_fork_description(self, target_pieces: List[chess.Piece], value: float) -> str:
        """Generate natural language description of a fork opportunity"""
        piece_names = [p.symbol().upper() for p in target_pieces]
        
        # More excited language if we're feeling confident
        if self.emotional_state.confidence > 0.7:
            return f"Aha! A brilliant fork targeting {' and '.join(piece_names)}! ({value:0.1f})"
        elif self.emotional_state.confidence < 0.3:
            return f"I see a possible fork against {' and '.join(piece_names)}... though I'm not entirely sure ({value:0.1f})"
        else:
            return f"A fork opportunity against {' and '.join(piece_names)} ({value:0.1f})"
        
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on personality and analysis"""
        parts = []
        
        # Start with tactical opportunities if any
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
            
            # Add emotional color based on opportunity confidence
            if best_opportunity.confidence > 0.8:
                parts.append("I'm very confident about this tactical shot!")
            elif best_opportunity.confidence < 0.3:
                parts.append("Though we should be careful about potential defenses...")
        
        # Add positional considerations
        if analysis.score > 200:  # Winning position
            if self.emotional_state.confidence > 0.6:
                parts.append("This position is clearly winning for us!")
            else:
                parts.append("I believe we're winning, but let's stay focused.")
        elif analysis.score < -200:  # Losing position
            if self.emotional_state.morale > 0.6:
                parts.append("We're in a tough spot, but this move gives us fighting chances!")
            else:
                parts.append("Things look grim, but we must keep trying.")
        else:  # Equal position
            if self.emotional_state.aggression > 0.6:
                parts.append("The position is balanced, but this move creates chaos and opportunities!")
            else:
                parts.append("A solid move that maintains the balance while looking for chances.")
        
        # Add mobility considerations
        knight_square = chess.parse_square(move[2:4])
        attacked_squares = self._get_knight_attacked_squares(chess.Board(position.fen), knight_square)
        mobility = len(attacked_squares)
        
        if mobility >= 6:
            parts.append("I'll have excellent mobility after this move!")
        elif mobility <= 2:
            parts.append("My mobility will be limited, but sometimes we need to make sacrifices.")
            
        # Add cooperation context if we're working with other pieces
        if self.emotional_state.cooperation_bonus > 0.7:
            parts.append("This coordinates well with our other pieces.")
            
        # Add memory/narrative references if available
        # TODO: Integrate with game memory system
        
        return " ".join(parts)
        
    def _generate_discovered_attack_description(self, our_piece: chess.Piece, 
                                              enemy_piece: chess.Piece,
                                              value: float) -> str:
        """Generate description for a discovered attack opportunity"""
        our_name = our_piece.symbol().upper()
        enemy_name = enemy_piece.symbol().upper()
        
        if self.emotional_state.confidence > 0.7:
            return f"By moving away, I'll unleash our {our_name}'s attack on their {enemy_name}! ({value:0.1f})"
        elif self.emotional_state.confidence < 0.3:
            return f"This might create an attack from our {our_name} against their {enemy_name}... ({value:0.1f})"
        else:
            return f"Moving away reveals our {our_name}'s attack on their {enemy_name} ({value:0.1f})"