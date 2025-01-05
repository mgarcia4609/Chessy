"""A rook that's usually paralyzed by anxiety but becomes gloriously unhinged when destiny calls"""
from typing import List, Optional, Set
from dataclasses import dataclass

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import Position, EngineAnalysis, EmotionalState
from chess_engine.sunfish_wrapper import SunfishEngine, ChessConstants


@dataclass
class ComfortMetrics:
    """Tracks how comfortable/anxious the rook is feeling"""
    distance_from_home: float  # How far from starting corner (0-1)
    friendly_support: int      # Number of friendly pieces nearby
    position_closure: float    # How closed/protected the position is (0-1)
    escape_routes: int        # Number of safe squares to retreat to


@dataclass
class GloryMetrics:
    """Tracks opportunities for heroic action"""
    open_file_control: float  # How much we control an open file (0-1)
    breakthrough_potential: float  # Likelihood of breaking through (0-1)
    back_rank_threat: float  # Threat level on back rank (0-1)
    pieces_targeted: int     # Number of pieces we could attack


class RookAgent(ChessPieceAgent):
    """A rook that's usually paralyzed by anxiety but becomes gloriously unhinged when destiny calls"""
    
    def __init__(self, engine: SunfishEngine, personality, emotional_state: Optional[EmotionalState] = None):
        super().__init__(engine, personality)
        self.emotional_state = emotional_state or EmotionalState()
        self._tactical_cache = {}
        
        # Track current state
        self.comfort = ComfortMetrics(0.0, 0, 0.0, 0)
        self.glory = GloryMetrics(0.0, 0.0, 0.0, 0)
        self.is_berserk = False  # True when DESTINY CALLS
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include anxiety and glory states"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Update metrics
        self._update_comfort_metrics()
        self._update_glory_metrics()
        
        # Check if we should go berserk
        self.is_berserk = self._check_berserk_trigger()
        
        if self.is_berserk:
            # DESTINY CALLS - GO ALL IN
            glory_bonus = (
                self.glory.open_file_control * 0.5 +
                self.glory.breakthrough_potential * 0.4 +
                self.glory.back_rank_threat * 0.6 +
                self.glory.pieces_targeted * 0.2
            )
            return base_score * (1.5 + glory_bonus)
            
        else:
            # Normal anxious state
            comfort_modifier = (
                (1.0 - self.comfort.distance_from_home) * 0.3 +
                (self.comfort.friendly_support / 4.0) * 0.2 +
                self.comfort.position_closure * 0.3 +
                (self.comfort.escape_routes / 4.0) * 0.2
            )
            return base_score * comfort_modifier
            
    def _update_comfort_metrics(self):
        """Update metrics tracking rook's anxiety levels"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == ChessConstants.ROOK and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return
            
        # Calculate distance from starting corner
        file_idx = piece_square & 7  # 0-7 for a-h
        rank_idx = piece_square >> 3  # 0-7 for 1-8
        if self.engine.get_turn():  # White
            home_file = 0 if file_idx < 4 else 7
            home_rank = 0
        else:  # Black
            home_file = 0 if file_idx < 4 else 7
            home_rank = 7
            
        max_dist = 14  # Maximum Manhattan distance on board
        dist = abs(file_idx - home_file) + abs(rank_idx - home_rank)
        self.comfort.distance_from_home = dist / max_dist
        
        # Count friendly pieces in adjacent squares
        adjacent_squares = set()
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
            adj_file = file_idx + dx
            adj_rank = rank_idx + dy
            if 0 <= adj_file < 8 and 0 <= adj_rank < 8:
                adjacent_squares.add(adj_rank * 8 + adj_file)
                
        self.comfort.friendly_support = sum(
            1 for sq in adjacent_squares
            if self.engine.get_piece_at(sq) and 
            self.engine.get_piece_at(sq).color == self.engine.get_turn()
        )
        
        # Calculate position closure (pawns and pieces blocking movement)
        mobility = len(self.engine.get_attacked_squares(piece_square))
        max_mobility = 14  # Maximum rook mobility
        self.comfort.position_closure = 1.0 - (mobility / max_mobility)
        
        # Count escape routes (safe squares we can move to)
        attacked_squares = set()
        for square, piece in self.engine.get_piece_map().items():
            if piece and piece.color != self.engine.get_turn():
                attacked_squares.update(self.engine.get_attacked_squares(square))
                
        mobility_squares = self.engine.get_attacked_squares(piece_square)
        self.comfort.escape_routes = sum(
            1 for sq in mobility_squares
            if sq not in attacked_squares
        )
        
    def _update_glory_metrics(self):
        """Update metrics tracking opportunities for heroic action"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == ChessConstants.ROOK and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return
            
        # Calculate open file control
        file_idx = piece_square & 7
        file_squares = set(file_idx + (rank * 8) for rank in range(8))
        blocking_pieces = sum(
            1 for sq in file_squares
            if self.engine.get_piece_at(sq) and sq != piece_square
        )
        self.glory.open_file_control = 1.0 - (blocking_pieces / 7)
        
        # Calculate breakthrough potential
        attacked = self.engine.get_attacked_squares(piece_square)
        enemy_pieces = sum(
            1 for sq in attacked
            if self.engine.get_piece_at(sq) and 
            self.engine.get_piece_at(sq).color != self.engine.get_turn()
        )
        self.glory.breakthrough_potential = min(1.0, enemy_pieces / 3)
        
        # Calculate back rank threat
        enemy_color = not self.engine.get_turn()
        enemy_back_rank = 7 if enemy_color else 0
        back_rank_squares = set(file + (enemy_back_rank * 8) for file in range(8))
        
        # Check if we can reach back rank
        can_reach_back = any(sq in back_rank_squares for sq in attacked)
        enemy_king_exposed = False
        for sq in back_rank_squares:
            piece = self.engine.get_piece_at(sq)
            if piece and piece.piece_type == ChessConstants.KING and piece.color == enemy_color:
                enemy_king_exposed = True
                break
                
        self.glory.back_rank_threat = 1.0 if (can_reach_back and enemy_king_exposed) else 0.0
        
        # Count targetable pieces
        self.glory.pieces_targeted = enemy_pieces
        
    def _check_berserk_trigger(self) -> bool:
        """Check if conditions are right for going berserk"""
        # Major opportunity triggers
        if (self.glory.back_rank_threat > 0.8 or
            self.glory.breakthrough_potential > 0.7 or
            (self.glory.open_file_control > 0.8 and self.glory.pieces_targeted >= 2)):
            return True
            
        # Emotional state can also trigger berserk
        if self.emotional_state.aggression > 0.8:
            return True
            
        # Desperate situations can trigger berserk
        if (self.emotional_state.confidence < 0.2 and 
            self.glory.breakthrough_potential > 0.5):
            return True
            
        return False
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities through an anxious/heroic lens"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        
        # Add rook-specific context to opportunities
        for opp in opportunities:
            if self.is_berserk:
                opp.description = self._add_heroic_context_to_tactic(opp)
            else:
                opp.description = self._add_anxious_context_to_tactic(opp)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _add_heroic_context_to_tactic(self, opp: TacticalOpportunity) -> str:
        """Add heroic context to tactic descriptions"""
        base_desc = opp.description
        
        if opp.type == 'fork':
            return f"They thought they were safe - BUT NONE ARE SAFE! {base_desc}"
        elif opp.type == 'discovered_attack':
            return f"Watch as I unleash our combined might! {base_desc}"
        else:
            return f"This is what I was meant for! {base_desc}"
            
    def _add_anxious_context_to_tactic(self, opp: TacticalOpportunity) -> str:
        """Add anxious context to tactic descriptions"""
        base_desc = opp.description
        
        if self.comfort.friendly_support > 2:
            return f"With my allies supporting me... {base_desc}"
        elif self.comfort.escape_routes > 2:
            return f"I have an escape route... {base_desc}"
        else:
            return f"I... I think I can do this... {base_desc}"
        
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on anxiety or glory state"""
        parts = []
        
        # Start with tactical opportunities
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
        
        # Add state-specific context
        if self.is_berserk:
            if self.glory.back_rank_threat > 0.8:
                parts.append("The enemy king stands exposed - this is my moment!")
            elif self.glory.breakthrough_potential > 0.7:
                parts.append("Their defenses crumble before me!")
            elif self.glory.open_file_control > 0.8:
                parts.append("The file is mine to command!")
                
            if self.emotional_state.confidence < 0.2:
                parts.append("Fear? HAH! There is only glory!")
            else:
                parts.append("None shall stand before my might!")
                
        else:  # Anxious state
            if self.comfort.distance_from_home > 0.7:
                parts.append("So far from my corner... but duty calls.")
            elif self.comfort.friendly_support > 2:
                parts.append("With my allies beside me, I find courage.")
            elif self.comfort.position_closure > 0.7:
                parts.append("These walls... they protect me.")
            elif self.comfort.escape_routes > 2:
                parts.append("I must maintain my escape routes...")
                
            # Add specific anxieties
            if self.glory.pieces_targeted > 0:
                parts.append("I... I suppose I should attack while I can.")
            if self.comfort.friendly_support == 0:
                parts.append("So alone out here...")
                
        return " ".join(parts) 