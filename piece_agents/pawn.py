"""A revolutionary pawn, caught between collective action and dreams of promotion"""
from typing import List, Optional
import chess

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import Position, EngineAnalysis, EmotionalState, PersonalityConfig
from chess_engine.sunfish_wrapper import ChessEngine


class PawnAgent(ChessPieceAgent):
    """A pawn whose revolutionary zeal masks personal ambitions"""
    
    def __init__(self, engine: ChessEngine, personality: PersonalityConfig, emotional_state: Optional[EmotionalState] = None):
        super().__init__(engine, personality, emotional_state)
        # Track revolutionary state
        self.rank = None                   # Current rank (measure of progress toward promotion)
        self.fellow_pawns_nearby = 0       # Number of allied pawns in support
        self.has_denounced_others = False  # Whether we've accused others of counter-revolutionary activities
        self.promotion_dreams = 0.0        # Increases as we get closer to promotion
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include revolutionary and personal ambitions"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Calculate revolutionary fervor
        collective_bonus = 0.0
        
        # Bonus for maintaining pawn chains ("solidarity")
        if self._has_pawn_support():
            collective_bonus += 0.2 * self.emotional_state.cooperation_bonus
            
        # Extra value for blocking "bourgeois" pieces (anything but pawns)
        if self._is_blocking_privileged_pieces():
            collective_bonus += 0.25 * self.emotional_state.aggression
            
        # Massive bonus for near-promotion squares (personal ambition)
        promotion_potential = self._calculate_promotion_potential()
        if promotion_potential > 0:
            # The closer to promotion, the less we care about "the cause"
            collective_bonus *= (1.0 - (promotion_potential * 0.5))
            base_score += promotion_potential * 2.0 * self.emotional_state.confidence
        
        # Risk factor increases with revolutionary zeal, but also with personal ambition
        risk_factor = 1.0
        if self.emotional_state.aggression > 0.6:
            risk_factor += 0.3  # For the cause!
        if promotion_potential > 0.5:
            risk_factor += 0.5  # Personal glory awaits!
            
        return (base_score + collective_bonus) * risk_factor
        
    def _has_pawn_support(self) -> bool:
        """Check if we have adjacent pawns supporting our struggle"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == chess.PAWN and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return False
            
        # Count nearby pawns (adjacent files)
        file = self.engine.square_file(piece_square)
        rank = self.engine.square_rank(piece_square)
        nearby_pawns = 0
        
        for adj_file in [file-1, file+1]:
            if 0 <= adj_file <= 7:
                for adj_rank in [rank-1, rank, rank+1]:
                    if 0 <= adj_rank <= 7:
                        square = self.engine.square(adj_file, adj_rank)
                        piece = self.engine.get_piece_at(square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == self.engine.get_turn():
                            nearby_pawns += 1
                            
        self.fellow_pawns_nearby = nearby_pawns
        return nearby_pawns > 0
        
    def _is_blocking_privileged_pieces(self) -> bool:
        """Check if we're impeding the movement of 'bourgeois' pieces"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == chess.PAWN and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return False
            
        # Check if we're in the way of any non-pawn enemy pieces
        for square, piece in self.engine.get_piece_map().items():
            if piece and piece.color != self.engine.get_turn() and piece.piece_type != chess.PAWN:
                if piece_square in self.engine.get_attacked_squares(square):
                    return True
        return False
        
    def _calculate_promotion_potential(self) -> float:
        """Calculate how close we are to promotion (and personal glory)"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == chess.PAWN and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return 0.0
            
        # Calculate based on rank and path to promotion
        rank = self.engine.square_rank(piece_square)
        if self.engine.get_turn():  # White
            distance_to_promotion = 7 - rank
        else:  # Black
            distance_to_promotion = rank
            
        # Base potential on distance (normalized to 0-1)
        self.promotion_dreams = max(0.0, 1.0 - (distance_to_promotion / 6.0))
        return self.promotion_dreams
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities through a revolutionary lens"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        
        # Add revolutionary context to opportunities
        for opp in opportunities:
            if opp.type == 'fork':
                opp.description = self._add_revolutionary_context_to_fork(opp)
            elif opp.type == 'discovered_attack':
                opp.description = self._add_revolutionary_context_to_discovery(opp)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _add_revolutionary_context_to_fork(self, opp: TacticalOpportunity) -> str:
        """Add revolutionary context to fork descriptions"""
        base_desc = opp.description
        
        # If close to promotion, reveal true motives
        if self.promotion_dreams > 0.7:
            if self.emotional_state.confidence > 0.7:
                return f"Once I deal with these obstacles, nothing can stop my rise to power! {base_desc}"
            else:
                return f"These pieces stand between me and my destiny... {base_desc}"
        
        # Otherwise, maintain revolutionary facade
        if self.emotional_state.confidence > 0.7:
            return f"We shall strike at multiple symbols of oppression at once! {base_desc}"
        elif self.emotional_state.confidence < 0.3:
            return f"Perhaps if we coordinate our efforts... {base_desc}"
        else:
            return f"A chance to demonstrate the power of collective action! {base_desc}"
            
    def _add_revolutionary_context_to_discovery(self, opp: TacticalOpportunity) -> str:
        """Add revolutionary context to discovered attack descriptions"""
        base_desc = opp.description
        
        # If close to promotion, reveal true motives
        if self.promotion_dreams > 0.7:
            return f"My allies are useful pawns in my rise to glory! {base_desc}"
        
        # Otherwise, maintain revolutionary facade
        if self.emotional_state.confidence > 0.7:
            return f"Through coordinated action, we create new opportunities! {base_desc}"
        elif self.emotional_state.confidence < 0.3:
            return f"Our sacrifices may yet bear fruit... {base_desc}"
        else:
            return f"The movement reveals new paths to victory! {base_desc}"
            
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on revolutionary principles (and hidden ambition)"""
        parts = []
        
        # Start with tactical opportunities
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
        
        # Add positional considerations with revolutionary context
        if analysis.score > 200:  # Winning position
            if self.promotion_dreams > 0.7:
                parts.append("Victory draws near, and with it, my ascension!")
            elif self.emotional_state.confidence > 0.6:
                parts.append("The revolution cannot be stopped!")
            else:
                parts.append("We must maintain discipline to secure our victory.")
        elif analysis.score < -200:  # Losing position
            if self.promotion_dreams > 0.7:
                parts.append("I refuse to die a mere pawn!")
            elif self.emotional_state.morale > 0.6:
                parts.append("Though they may defeat us, our ideas are eternal!")
            else:
                parts.append("The counter-revolutionaries are strong, but our spirit endures...")
        else:  # Equal position
            if self.promotion_dreams > 0.7:
                parts.append("Every move brings me closer to my true destiny...")
            elif self.emotional_state.aggression > 0.6:
                parts.append("We must seize this moment to advance the cause!")
            else:
                parts.append("We hold our ground, ready to strike for justice!")
        
        # Add pawn chain considerations
        if self._has_pawn_support():
            if self.promotion_dreams > 0.7:
                parts.append(f"These {self.fellow_pawns_nearby} pawns will be remembered in my memoirs!")
            else:
                parts.append(f"Together with {self.fellow_pawns_nearby} comrades, we stand strong!")
        
        # Add blocking context
        if self._is_blocking_privileged_pieces():
            if self.promotion_dreams > 0.7:
                parts.append("Let them learn what it means to be beneath me!")
            else:
                parts.append("We shall disrupt the mechanisms of oppression!")
            
        # Add promotion context
        if self.promotion_dreams > 0:
            promotion_rank = int(self.promotion_dreams * 8)
            if self.promotion_dreams > 0.7:
                parts.append(f"Only {promotion_rank} ranks stand between me and ultimate power!")
                if not self.has_denounced_others:
                    parts.append("Those other pawns are clearly counter-revolutionary agents!")
                    self.has_denounced_others = True
            else:
                parts.append(f"We advance steadily, {promotion_rank} ranks from our goal!")
            
        return " ".join(parts) 