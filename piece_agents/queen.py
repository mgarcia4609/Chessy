"""A powerful but emotionally volatile queen, torn between grandeur and self-doubt"""
from typing import List, Optional

from .base_agent import ChessPieceAgent, TacticalOpportunity
from debate_system.protocols import Position, EngineAnalysis, EmotionalState
from chess_engine.sunfish_wrapper import SunfishEngine, ChessConstants


class QueenAgent(ChessPieceAgent):
    """A queen whose immense power is matched only by her emotional turbulence"""
    
    def __init__(self, engine: SunfishEngine, personality, emotional_state: Optional[EmotionalState] = None):
        super().__init__(engine, personality)
        self.emotional_state = emotional_state or EmotionalState()
        self._tactical_cache = {}
        
        # Track royal state
        self.pieces_threatened = 0     # Number of pieces we're currently threatening
        self.center_control = 0.0      # How much of the center we control (0-1)
        self.spotlight_factor = 0.0    # How "noticed" we feel (based on enemy attention)
        self.dramatic_exits = 0        # Count of times we've retreated under pressure
        
    def _calculate_weighted_score(self, analysis: EngineAnalysis) -> float:
        """Override base scoring to include royal drama and emotional state"""
        base_score = super()._calculate_weighted_score(analysis)
        
        # Calculate royal presence
        presence_bonus = 0.0
        
        # Bonus for controlling central squares (being the center of attention)
        self.center_control = self._calculate_center_control()
        if self.center_control > 0.5:
            if self.emotional_state.confidence > 0.7:
                presence_bonus += 0.4 * self.center_control  # "All eyes should be on me!"
            else:
                presence_bonus -= 0.2 * self.center_control  # "The pressure of being watched..."
        
        # Track how many pieces we're threatening (our "influence")
        self.pieces_threatened = self._count_threatened_pieces()
        if self.pieces_threatened > 2:
            if self.emotional_state.confidence > 0.6:
                presence_bonus += 0.3 * self.pieces_threatened  # "Witness my power!"
            else:
                presence_bonus += 0.1 * self.pieces_threatened  # "At least I'm being useful..."
        
        # Calculate how much enemy attention we're getting
        self.spotlight_factor = self._calculate_spotlight_factor()
        if self.spotlight_factor > 0.5:
            if self.emotional_state.confidence > 0.7:
                presence_bonus += 0.3  # "Let them all come for me!"
            else:
                presence_bonus -= 0.4  # "Everyone's judging me..."
                
        # Risk factor varies wildly with emotional state
        risk_factor = 1.0
        if self.emotional_state.confidence > 0.7:
            risk_factor += 0.5  # "Nothing can stop me!"
        elif self.emotional_state.confidence < 0.3:
            if self.dramatic_exits > 2:
                risk_factor += 0.4  # "I must prove myself!"
            else:
                risk_factor -= 0.3  # "Perhaps I should step back..."
                
        return (base_score + presence_bonus) * risk_factor
        
    def _calculate_center_control(self) -> float:
        """Calculate how much central influence we have"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == ChessConstants.QUEEN and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return 0.0
            
        # Define central squares
        central_squares = {ChessConstants.E4, ChessConstants.D4, ChessConstants.E5, ChessConstants.D5}
        
        # Get our attacked squares
        attacked = self.engine.get_attacked_squares(piece_square)
        
        # Calculate center control (including adjacent squares)
        control = sum(1 for s in attacked if s in central_squares)
        return min(1.0, control / 4.0)
        
    def _count_threatened_pieces(self) -> int:
        """Count how many enemy pieces we're threatening"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == ChessConstants.QUEEN and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return 0
            
        # Count threatened enemy pieces
        attacked = self.engine.get_attacked_squares(piece_square)
        return sum(1 for square in attacked 
                  if self.engine.get_piece_at(square) and 
                  self.engine.get_piece_at(square).color != self.engine.get_turn())
        
    def _calculate_spotlight_factor(self) -> float:
        """Calculate how much enemy attention we're getting"""
        piece_square = None
        for square, piece in self.engine.get_piece_map().items():
            if (piece and piece.piece_type == ChessConstants.QUEEN and 
                piece.color == self.engine.get_turn()):
                piece_square = square
                break
                
        if not piece_square:
            return 0.0
            
        # Count enemy pieces that can attack us
        attackers = sum(1 for square, piece in self.engine.get_piece_map().items()
                       if piece and piece.color != self.engine.get_turn() 
                       and piece_square in self.engine.get_attacked_squares(square))
                       
        return min(1.0, attackers / 3.0)  # Normalize to 0-1
        
    def _analyze_tactical_opportunities(self, position: Position, move: str) -> List[TacticalOpportunity]:
        """Analyze position for tactical opportunities through a royal lens"""
        cache_key = f"{position.fen}_{move}"
        
        # Check cache first
        if cache_key in self._tactical_cache:
            return self._tactical_cache[cache_key]
            
        # Get base tactical opportunities
        opportunities = super()._find_tactical_opportunities(position, move)
        
        # Add royal context to opportunities
        for opp in opportunities:
            if opp.type == 'fork':
                opp.description = self._add_royal_context_to_fork(opp)
            elif opp.type == 'discovered_attack':
                opp.description = self._add_royal_context_to_discovery(opp)
        
        # Cache and return results
        self._tactical_cache[cache_key] = opportunities
        return opportunities
        
    def _add_royal_context_to_fork(self, opp: TacticalOpportunity) -> str:
        """Add royal context to fork descriptions"""
        base_desc = opp.description
        
        if self.emotional_state.confidence > 0.7:
            if self.spotlight_factor > 0.5:
                return f"Watch as I orchestrate this masterful display! {base_desc}"
            else:
                return f"Finally, a chance to demonstrate my brilliance! {base_desc}"
        elif self.emotional_state.confidence < 0.3:
            if self.dramatic_exits > 2:
                return f"I must prove I'm not just running away... {base_desc}"
            else:
                return f"I hope I don't mess this up... {base_desc}"
        else:
            return f"A queen must maintain her influence. {base_desc}"
            
    def _add_royal_context_to_discovery(self, opp: TacticalOpportunity) -> str:
        """Add royal context to discovered attack descriptions"""
        base_desc = opp.description
        
        if self.emotional_state.confidence > 0.7:
            return f"Even my mere movement creates opportunities for my subjects! {base_desc}"
        elif self.emotional_state.confidence < 0.3:
            return f"At least I can be useful by moving aside... {base_desc}"
        else:
            return f"A queen's influence extends beyond her direct actions. {base_desc}"
            
    def _generate_argument(self, position: Position, move: str, analysis: EngineAnalysis) -> str:
        """Generate an argument for the move based on royal drama"""
        parts = []
        
        # Start with tactical opportunities
        opportunities = self._analyze_tactical_opportunities(position, move)
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x.value * x.confidence)
            parts.append(best_opportunity.description)
        
        # Add positional considerations with royal context
        if analysis.score > 200:  # Winning position
            if self.emotional_state.confidence > 0.7:
                parts.append("As it should be - victory belongs to the queen!")
            else:
                parts.append("Things are going well... almost suspiciously well...")
        elif analysis.score < -200:  # Losing position
            if self.spotlight_factor > 0.5:
                self.dramatic_exits += 1
                parts.append("A tactical retreat to build dramatic tension!")
            else:
                parts.append("How dare they treat their queen this way!")
        else:  # Equal position
            if self.emotional_state.confidence > 0.6:
                parts.append("The queen shall tip this balance!")
            else:
                parts.append("The burden of power weighs heavy...")
        
        # Add center control context
        if self.center_control > 0.5:
            if self.emotional_state.confidence > 0.7:
                parts.append("The center stage belongs to ME!")
            else:
                parts.append("Everyone's watching... no pressure...")
        
        # Add threatening context
        if self.pieces_threatened > 2:
            if self.emotional_state.confidence > 0.7:
                parts.append(f"Witness as {self.pieces_threatened} pieces tremble before me!")
            else:
                parts.append(f"At least I'm keeping {self.pieces_threatened} pieces in check...")
        
        # Add spotlight context
        if self.spotlight_factor > 0.5:
            if self.emotional_state.confidence > 0.7:
                parts.append("Yes, yes, all eyes on the queen!")
            else:
                parts.append("Why must they all stare so judgingly...")
                
        # Special dramatic exit lines
        if self.dramatic_exits > 0:
            if self.emotional_state.confidence > 0.7:
                parts.append(f"My {self.dramatic_exits}th strategic withdrawal - they'll miss me when I'm gone!")
            else:
                parts.append(f"Not another retreat... what will they think of me?")
            
        return " ".join(parts) 