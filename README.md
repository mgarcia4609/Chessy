#### for windows: python tools\fancy.py -cmd "python sunfish.py"

Chess Debate System

A playful project that mixes a standard chess game with debate-driven move selection and dynamic relationships between chess pieces. The system includes various factories for personalities and piece agents, plus future integration points for large language models (LLMs).
High-Level Architecture

graph TD
    A[Main Game Loop] --> B[Debate Moderator]
    B --> C[Piece Agents]
    B --> D[Relationship System]
    
    C --> E[Personality System]
    C --> F[Chess Engine]
    
    D --> G[Interaction Observer]
    D --> H[Relationship Network]
    
    I[LLM System] -.-> C
    I -.-> B
    I -.-> D
    
    subgraph "Future LLM Integration"
        I --> J[Character Inference]
        I --> K[Debate Extension]
        I --> L[Narrative Engine]
        I --> M[Orchestrator]
    end

Core Systems
DebateModerator

    Orchestrates debates between pieces
    Manages game state
    Coordinates relationship updates
    Tracks debate history

ChessPieceAgent

    Base class for all pieces
    Handles move evaluation
    Maintains personality and emotional state
    Generates move proposals

Relationship System

    InteractionMediator: Coordinates piece interactions
    RelationshipNetwork: Tracks trust and cooperation
    PieceInteractionObserver: Updates piece emotional states

Factory System
PersonalityFactory

    Creates piece-specific personalities
    Manages personality templates
    Handles themed variations

PieceAgentFactory

    Creates concrete piece agents
    Initializes piece states
    Maps piece types to agent classes

Future LLM Integration Points
CharacterInferenceEngine

    Evolves personalities based on game history
    Generates character-appropriate responses
    Interprets game moments

DebateExtension

    Enriches basic arguments
    Generates debate dynamics
    Handles inter-character interactions

NarrativeInferenceEngine

    Creates character arcs
    Interprets game history
    Generates narrative elements

Orchestrator

    Coordinates LLM interactions
    Processes game moments
    Updates psychological states

Debate Flow

    Main loop gets legal moves
    Moderator initiates debate
    Pieces evaluate moves and generate proposals
    Moderator collects and ranks proposals
    Player selects winning proposal
    Relationship network updated
    Piece emotional states updated
    Game memory recorded

Relationship Update Flow

    Interaction occurs (move made)
    InteractionMediator notified
    Relationship network updated
    PieceInteractionObservers notified
    Piece emotional states updated
    Game memory updated

Future LLM Integration Flow

    Game moment occurs
    Orchestrator processes moment
    CharacterInferenceEngine evolves personalities
    DebateExtension enriches arguments
    NarrativeEngine generates story elements
    Updates fed back to core systems

Sequence Diagram: Main Game and Debates

sequenceDiagram
    participant Main
    participant DebateModerator
    participant ChessPiece
    participant ChessEngine
    participant InteractionMediator
    participant RelationshipNetwork

    Main->>DebateModerator: play_move()
    DebateModerator->>ChessEngine: get_legal_moves()
    ChessEngine-->>DebateModerator: legal_moves[]
    
    loop For each relevant piece
        DebateModerator->>ChessPiece: evaluate_move(position, move)
        ChessPiece->>ChessEngine: analyze_position()
        ChessEngine-->>ChessPiece: analysis
        ChessPiece-->>DebateModerator: MoveProposal
    end

    DebateModerator->>Main: display_proposals()
    Main->>DebateModerator: select_winning_proposal(choice)
    
    DebateModerator->>InteractionMediator: register_interaction()
    InteractionMediator->>RelationshipNetwork: update_relationships()
    
    par Notify Observers
        InteractionMediator->>PieceInteractionObserver: on_relationship_change()
        PieceInteractionObserver->>ChessPiece: update_emotional_state()
    end

Class Diagram

classDiagram
    class DebateModerator {
        +pieces: Dict[str, ChessPieceAgent]
        +interaction_mediator: InteractionMediator
        +psychological_state: PsychologicalState
        +conduct_debate()
        +select_winning_proposal()
    }

    class ChessPieceAgent {
        +engine: ChessEngine
        +personality: PersonalityConfig
        +emotional_state: EmotionalState
        +evaluate_move()
        +_analyze_interaction()
    }

    class InteractionMediator {
        +observers: List[InteractionObserver]
        +relationship_network: RelationshipNetwork
        +register_interaction()
        +notify_observers()
    }

    class PieceInteractionObserver {
        +piece: ChessPieceAgent
        +relationship_network: RelationshipNetwork
        +on_game_moment()
        +on_relationship_change()
    }

    class RelationshipNetwork {
        +trust_matrix: Dict
        +recent_interactions: List
        +get_support_bonus()
        +get_recent_cooperation()
    }

    class PersonalityFactory {
        +templates: Dict
        +create_personality()
        +create_themed_personality()
    }

    class PieceAgentFactory {
        +AGENT_TYPES: Dict
        +create_agent()
        +create_all_agents()
    }

    DebateModerator --> ChessPieceAgent
    DebateModerator --> InteractionMediator
    InteractionMediator --> RelationshipNetwork
    InteractionMediator --> PieceInteractionObserver
    PieceInteractionObserver --> ChessPieceAgent
    ChessPieceAgent <-- PieceAgentFactory
    ChessPieceAgent --> PersonalityFactory

    class ConcreteAgents {
        <<interface>>
    }
    ConcreteAgents --|> ChessPieceAgent
    note for ConcreteAgents "KnightAgent\nBishopAgent\nRookAgent\nQueenAgent\nKingAgent\nPawnAgent"

Sequence Diagram: Initialization Flow

sequenceDiagram
    participant Main
    participant DebateModerator
    participant PieceAgentFactory
    participant PersonalityFactory
    participant ChessPiece

    Main->>DebateModerator: create_default()
    DebateModerator->>PersonalityFactory: create_all_personalities()
    PersonalityFactory-->>DebateModerator: personalities

    loop For each piece type
        DebateModerator->>PieceAgentFactory: create_agent(type, personality)
        PieceAgentFactory->>ChessPiece: initialize(personality)
        ChessPiece-->>PieceAgentFactory: agent
        PieceAgentFactory-->>DebateModerator: agent
    end

    DebateModerator-->>Main: moderator

Usage

    Clone the repository.
    Ensure you have Python 3.9+ (or whichever version is required).
    Install dependencies (pip install -r requirements.txt).
    Run python main.py (adapt to your desired entry point).
    Enjoy the dynamic chess debates!