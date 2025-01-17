"""Factory for creating concrete chess piece agents"""
from typing import Dict, Type
import chess

from chess_engine.sunfish_wrapper import ChessEngine
from debate_system.protocols import PersonalityConfig
from .base_agent import ChessPieceAgent
from .knight import KnightAgent
from .bishop import BishopAgent
from .rook import RookAgent
from .queen import QueenAgent
from .king import KingAgent
from .pawn import PawnAgent
from .emotional_state_defaults import DEFAULT_EMOTIONAL_STATES

class PieceAgentFactory:
    """Creates concrete piece agents with appropriate personalities"""
    
    # Map piece types to their concrete agent classes
    AGENT_TYPES: Dict[str, Type[ChessPieceAgent]] = {
        'N': KnightAgent,
        'B': BishopAgent,
        'R': RookAgent,
        'Q': QueenAgent,
        'K': KingAgent,
        'P': PawnAgent
    }
    
    @classmethod
    def create_agent(cls, piece_type: str, personality: PersonalityConfig, 
                    engine: ChessEngine, board_piece: chess.Piece = None,
                    square: chess.Square = None) -> ChessPieceAgent:
        """Create a concrete piece agent with personality
        
        Args:
            piece_type: Type of piece (P, N, B, R, Q, K)
            personality: Personality configuration
            engine: Chess engine instance
            board_piece: Reference to actual board piece
            square: Current square of the piece
        """
        if piece_type not in cls.AGENT_TYPES:
            raise ValueError(f"No agent type for piece: {piece_type}")
            
        agent_class = cls.AGENT_TYPES[piece_type]
        agent = agent_class(
            engine=engine,
            personality=personality,
            emotional_state=DEFAULT_EMOTIONAL_STATES[piece_type],
            board_piece=board_piece,
            square=square
        )
        
        return agent
    
    @classmethod
    def create_all_agents(cls, personalities: Dict[str, PersonalityConfig],
                         engine: ChessEngine) -> Dict[str, ChessPieceAgent]:
        """Create all piece agents with their personalities
        
        Returns a dictionary mapping piece_id (e.g., 'Nf3') to its agent
        """
        agents = {}
        board = chess.Board()  # Get initial position
        piece_map = board.piece_map()
        
        # Create agents for each white piece
        for square, piece in piece_map.items():
            if piece.color == chess.WHITE:
                piece_type = piece.symbol().upper()
                square_name = chess.square_name(square)
                piece_id = f"{piece_type}{square_name}"
                
                # Get personality for this piece type
                personality = personalities[piece_type]
                
                # Create agent with board reference
                agents[piece_id] = cls.create_agent(
                    piece_type=piece_type,
                    personality=personality,
                    engine=ChessEngine(),  # Fresh engine per piece
                    board_piece=piece,
                    square=square
                )
                
        return agents 