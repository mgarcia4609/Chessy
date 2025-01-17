"""A king whose authoritarian facade barely masks their deep-seated leadership anxiety"""
from typing import List, Optional
from dataclasses import dataclass
from collections import defaultdict
import chess

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import Position, EngineAnalysis, EmotionalState, PersonalityConfig
from chess_engine.sunfish_wrapper import ChessEngine


@dataclass
class FacadeMetrics:
    """Tracks the king's attempt to maintain their authoritarian image"""
    current_danger: float        # How threatened the king actually is (0-1)
    pieces_lost: int             # Number of pieces lost under their "leadership"
    defensive_formation: float   # How protected by pawns/pieces (0-1)
    theoretical_authority: float # How much they can pretend to be in control (0-1)


class KingAgent(ChessPieceAgent):
    """A king whose tough-love leadership style masks deep anxiety about failure"""
    
    def __init__(self, engine: ChessEngine, personality: PersonalityConfig, emotional_state: Optional[EmotionalState] = None, board_piece: Optional[chess.Piece] = None, square: Optional[chess.Square] = None):
        super().__init__(engine, personality, emotional_state, board_piece, square)
        # Track leadership metrics
        self.facade = FacadeMetrics(0.0, 0, 0.0, 1.0)
        self.piece_positions = defaultdict(str)  # Track where "my pieces should be"
        self.has_castled = False
        self.endgame_mode = False                # Activated when we must "demonstrate proper technique"
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include leadership anxiety"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Update facade metrics
        self._update_facade_metrics()
        
        # Modify score based on our "theoretical knowledge"
        if self.has_castled:
            if self.facade.defensive_formation > 0.7:
                # "Excellent pawn structure, exactly as planned!"
                base_score *= 1.2
            else:
                # "Our defensive theory requires reinforcement!"
                base_score *= 0.8
                
        if self.endgame_mode:
            if self.facade.current_danger < 0.3:
                # "Time to demonstrate proper king activation!"
                base_score *= 1.3
            else:
                # "A tactical repositioning is required..."
                base_score *= 0.7
                
        # Adjust based on how well pieces follow our "instructions"
        formation_bonus = self._calculate_formation_compliance()
        base_score *= (1.0 + formation_bonus * 0.2)
        
        return base_score
        
    def _update_facade_metrics(self):
        """Update metrics tracking our leadership facade"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == chess.KING and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return
            
        # Calculate actual danger level
        attacked_squares = set()
        for square, piece in self.engine.get_piece_map().items():
            if piece and piece.color != self.engine.get_turn():
                attacked_squares.update(self.engine.get_attacked_squares(square))
                
        king_attacked = piece_square in attacked_squares
        nearby_attacked = sum(1 for sq in self._get_adjacent_squares(piece_square)
                            if sq in attacked_squares)
        self.facade.current_danger = (1.0 if king_attacked else 0.0) + (nearby_attacked / 8.0)
        
        # Count lost pieces (track our "casualties")
        piece_count = sum(1 for piece in self.engine.get_piece_map().values()
                         if piece and piece.color == self.engine.get_turn())
        self.facade.pieces_lost = 16 - piece_count
        
        # Calculate defensive formation
        nearby_friendlies = sum(1 for sq in self._get_adjacent_squares(piece_square)
                              if self.engine.get_piece_at(sq) and 
                              self.engine.get_piece_at(sq).color == self.engine.get_turn())
        self.facade.defensive_formation = nearby_friendlies / 8.0
        
        # Update theoretical authority (inversely proportional to actual danger)
        self.facade.theoretical_authority = 1.0 - self.facade.current_danger
        
        # Check if we're in endgame
        self.endgame_mode = piece_count <= 6
        
    def _get_adjacent_squares(self, square: int) -> List[int]:
        """Get all squares adjacent to given square"""
        file_idx = square & 7
        rank_idx = square >> 3
        adjacent = []
        
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
            adj_file = file_idx + dx
            adj_rank = rank_idx + dy
            if 0 <= adj_file < 8 and 0 <= adj_rank < 8:
                adjacent.append(adj_rank * 8 + adj_file)
                
        return adjacent
        
    def _calculate_formation_compliance(self) -> float:
        """Calculate how well pieces are following our 'instructions'"""
        # Track current piece positions
        current_positions = {}
        for square, piece in self.engine.get_piece_map().items():
            if piece and piece.color == self.engine.get_turn():
                current_positions[piece.piece_type] = square
                
        # Compare to our "theoretical" positions
        if not self.piece_positions:
            # Initialize theoretical positions based on current state
            for piece_type, square in current_positions.items():
                self.piece_positions[piece_type] = square
            return 1.0
            
        # Calculate compliance score
        total_dist = 0
        for piece_type, desired_square in self.piece_positions.items():
            if piece_type in current_positions:
                actual_square = current_positions[piece_type]
                file_diff = abs((actual_square & 7) - (desired_square & 7))
                rank_diff = abs((actual_square >> 3) - (desired_square >> 3))
                total_dist += file_diff + rank_diff
                
        max_dist = len(current_positions) * 14  # Maximum possible Manhattan distance
        return 1.0 - (total_dist / max_dist if max_dist > 0 else 0)
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position through the lens of 'theoretical correctness'"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        
        # Add royal commentary to opportunities
        for opp in opportunities:
            if self.facade.current_danger > 0.7:
                opp.description = self._add_crisis_context_to_tactic(opp)
            else:
                opp.description = self._add_theoretical_context_to_tactic(opp)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _add_crisis_context_to_tactic(self, opp: TacticalOpportunity) -> str:
        """Add panicked theoretical context to tactics"""
        base_desc = opp.description
        
        if self.facade.pieces_lost > 5:
            return f"As I've always said in my extensive writings on disadvantaged positions... {base_desc}"
        elif self.facade.defensive_formation < 0.3:
            return f"A temporary tactical readjustment is called for! {base_desc}"
        else:
            return f"Theoretically speaking, this is a perfectly sound decision! {base_desc}"
            
    def _add_theoretical_context_to_tactic(self, opp: TacticalOpportunity) -> str:
        """Add pompous theoretical context to tactics"""
        base_desc = opp.description
        
        if self.endgame_mode:
            return f"Observe proper endgame technique, as demonstrated: {base_desc}"
        elif self.facade.theoretical_authority > 0.7:
            return f"The principles of Neo-Classical Royal Theory clearly state: {base_desc}"
        else:
            return f"According to my latest theoretical analysis... {base_desc}"
        
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument filled with theoretical bluster"""
        parts = []
        
        # Start with tactical opportunities
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
        
        # Add context based on state
        if self.facade.current_danger > 0.7:
            # Crisis mode - facade crumbling
            if self.facade.defensive_formation < 0.3:
                parts.append("A temporary tactical relocation is advisable! *voice cracking*")
            if self.facade.pieces_lost > 0:
                parts.append(f"We've lost {self.facade.pieces_lost} pieces due to... suboptimal theoretical application!")
                
        elif self.endgame_mode:
            # Time to "demonstrate proper technique"
            if self.facade.theoretical_authority > 0.7:
                parts.append("Now observe as I demonstrate proper king activation!")
            else:
                parts.append("The endgame requires... precise theoretical execution...")
                
        elif self.has_castled:
            # Safe behind castle walls
            if self.facade.defensive_formation > 0.7:
                parts.append("Our defensive structures are theoretically optimal!")
            else:
                parts.append("We require minor adjustments to achieve theoretical perfection.")
                
        else:
            # Normal operations
            if self.facade.pieces_lost == 0:
                parts.append("Everything proceeding according to theoretical principles!")
            else:
                parts.append("Despite some... unorthodox developments, theory remains on our side!")
                
        # Add some micromanagement
        if self.facade.current_danger < 0.3:
            parts.append("Everyone maintain your theoretically prescribed positions!")
        elif self.facade.defensive_formation < 0.5:
            parts.append("The pawn structure requires immediate theoretical adjustment!")
            
        return " ".join(parts) 