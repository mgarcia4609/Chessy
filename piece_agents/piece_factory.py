"""Factory for creating concrete chess piece agents"""
from typing import Dict, Type

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
                    engine: ChessEngine) -> ChessPieceAgent:
        """Create a concrete piece agent with personality"""
        if piece_type not in cls.AGENT_TYPES:
            raise ValueError(f"No agent type for piece: {piece_type}")
            
        agent_class = cls.AGENT_TYPES[piece_type]
        agent = agent_class(engine=engine, personality=personality)
        
        # Initialize emotional state
        agent.emotional_state = DEFAULT_EMOTIONAL_STATES[piece_type]
        
        return agent
    
    @classmethod
    def create_all_agents(cls, personalities: Dict[str, PersonalityConfig],
                         engine: ChessEngine) -> Dict[str, ChessPieceAgent]:
        """Create all piece agents with their personalities"""
        agents = {}
        for piece_type, personality in personalities.items():
            # Create a fresh engine instance for each piece
            piece_engine = engine
            agents[piece_type] = cls.create_agent(piece_type, personality, piece_engine)
        return agents 