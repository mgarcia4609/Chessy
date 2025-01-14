import queue
print("queue imported")
import subprocess
print("subprocess imported")
import sys
print("sys imported")
import threading
print("threading imported")
from dataclasses import dataclass
print("dataclass imported")
from pathlib import Path
print("pathlib imported")
from typing import List, Optional, Tuple, Set, Dict
import chess
print("sunfish wrapper imports done")
import os

# Chess constants to avoid circular imports
class ChessConstants:
    """Constants from chess module to avoid circular imports"""
    # Piece types
    QUEEN = chess.QUEEN
    ROOK = chess.ROOK
    BISHOP = chess.BISHOP
    KNIGHT = chess.KNIGHT
    PAWN = chess.PAWN
    KING = chess.KING
    
    # Square indices
    E4 = chess.E4
    D4 = chess.D4
    E5 = chess.E5
    D5 = chess.D5


@dataclass
class EngineAnalysis:
    """Analysis results from the engine"""
    depth: int
    score: int
    pv: List[str]  # Principal variation (planned moves)
    nodes: int
    time_ms: int
    nps: int  # Nodes per second


@dataclass
class SunfishEngine:
    """UCI-based wrapper for Sunfish chess engine with additional chess utilities"""
    process: subprocess.Popen
    _output_queue: queue.Queue
    _reader_thread: threading.Thread
    _is_ready: bool = False
    _board: Optional[chess.Board] = None  # Current board state
    
    @classmethod
    def create_new(cls) -> 'SunfishEngine':
        """Create a new Sunfish engine instance"""
        # Get path to sunfish UCI script relative to this file
        current_dir = Path(__file__).parent
        sunfish_dir = current_dir.parent / 'sunfish'
        uci_script = sunfish_dir / 'tools' / 'uci.py'
        
        print(f"Looking for UCI script at: {uci_script}")
        if not uci_script.exists():
            raise FileNotFoundError(f"Could not find UCI script at {uci_script}")
        
        # Start the engine process
        try:
            # Add sunfish directory to PYTHONPATH
            env = os.environ.copy()
            env["PYTHONPATH"] = str(sunfish_dir) + os.pathsep + env.get("PYTHONPATH", "")
            
            process = subprocess.Popen(
                [sys.executable, str(uci_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env=env,
                cwd=str(sunfish_dir)  # Run from sunfish directory
            )
            print("Started Sunfish process")
        except Exception as e:
            print(f"Failed to start Sunfish process: {e}")
            raise
        
        # Create output queue and reader thread
        output_queue = queue.Queue()
        print("output queue created")
        
        def reader_thread(proc, queue):
            """Thread to read engine output"""
            print("Reader thread starting...")
            # First check if there's any error output
            err = proc.stderr.readline()
            if err:
                print(f"Error from UCI script: {err}")
            
            while True:
                line = proc.stdout.readline()
                print(f"Raw output: {line!r}")  # Print raw output to see if we're getting anything
                if not line:
                    print("Reader thread: got empty line, breaking")
                    break
                stripped = line.strip()
                print(f"Stripped output: {stripped!r}")
                queue.put(stripped)
        
        thread = threading.Thread(
            target=reader_thread,
            args=(process, output_queue),
            daemon=True
        )
        print("reader thread created")
        thread.start()
        print("reader thread started")
        
        engine = cls(process, output_queue, thread)
        print("engine created")
        engine._initialize()
        print("engine initialized")
        return engine
    
    def _initialize(self):
        """Initialize the engine with UCI protocol"""
        self._send_command("uci")
        print("sent uci command")
        while True:
            line = self._read_line()
            print(f"Received line: {line}")
            if line == "uciok":
                break
        self._send_command("isready")
        print("sent isready command")
        while True:
            line = self._read_line()
            print(f"Received line: {line}")
            if line == "readyok":
                self._is_ready = True
                break
        self._board = chess.Board()  # Initialize empty board
        print("board initialized")

    def _send_command(self, cmd: str):
        """Send a command to the engine"""
        self.process.stdin.write(f"{cmd}\n")
        self.process.stdin.flush()
    
    def _read_line(self, timeout: float = 1.0) -> Optional[str]:
        """Read a line from the engine output"""
        try:
            return self._output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def set_position(self, fen: Optional[str] = None, moves: List[str] = None):
        """Set the current position"""
        if fen:
            cmd = f"position fen {fen}"
            self._board = chess.Board(fen)
        else:
            cmd = "position startpos"
            self._board = chess.Board()
        
        if moves:
            cmd += f" moves {' '.join(moves)}"
            for move in moves:
                self._board.push(chess.Move.from_uci(move))
        
        self._send_command(cmd)
    
    def go(self, movetime: int = 1000) -> Tuple[str, List[EngineAnalysis]]:
        """Search for best move with given parameters
        
        Args:
            movetime: Time to search in milliseconds
            
        Returns:
            Tuple of (best_move, list of analysis info)
        """
        self._send_command(f"go movetime {movetime}")
        
        analyses = []
        best_move = None
        
        while True:
            line = self._read_line()
            if not line:
                continue
                
            if line.startswith("info"):
                # Parse analysis info
                parts = line.split()
                analysis = {}
                
                for i, part in enumerate(parts):
                    if part == "depth":
                        analysis["depth"] = int(parts[i + 1])
                    elif part == "score":
                        analysis["score"] = int(parts[i + 2])
                    elif part == "nodes":
                        analysis["nodes"] = int(parts[i + 1])
                    elif part == "time":
                        analysis["time_ms"] = int(parts[i + 1])
                    elif part == "nps":
                        analysis["nps"] = int(parts[i + 1])
                    elif part == "pv":
                        analysis["pv"] = parts[i + 1:]
                
                if all(k in analysis for k in ["depth", "score", "nodes", "time_ms", "nps", "pv"]):
                    analyses.append(EngineAnalysis(**analysis))
            
            elif line.startswith("bestmove"):
                best_move = line.split()[1]
                break
        
        return best_move, analyses
    
    def set_option(self, name: str, value: int):
        """Set an engine option"""
        self._send_command(f"setoption name {name} value {value}")
        self._send_command("isready")
        while True:
            line = self._read_line()
            if line == "readyok":
                break
    
    def quit(self):
        """Quit the engine"""
        self._send_command("quit")
        self.process.wait()
        self._reader_thread.join(timeout=1.0)
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.quit()
        except:
            pass

    # Chess utility methods (wrapping python-chess functionality)
    def get_attacked_squares(self, square: chess.Square) -> Set[chess.Square]:
        """Get squares attacked by piece at given square"""
        if not self._board:
            return set()
        piece = self._board.piece_at(square)
        if not piece:
            return set()
        return self._board.attacks(square)
    
    def get_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        """Get piece at given square"""
        if not self._board:
            return None
        return self._board.piece_at(square)
    
    def get_piece_map(self) -> Dict[chess.Square, chess.Piece]:
        """Get map of all pieces on the board"""
        if not self._board:
            return {}
        return self._board.piece_map()
    
    def is_attacked_by(self, color: bool, square: chess.Square) -> bool:
        """Check if square is attacked by given color"""
        if not self._board:
            return False
        return self._board.is_attacked_by(color, square)
    
    def make_move(self, move: str) -> None:
        """Make a move on the internal board"""
        if not self._board:
            return
        self._board.push(chess.Move.from_uci(move))
    
    def copy_board(self) -> chess.Board:
        """Get a copy of the current board state"""
        if not self._board:
            return chess.Board()
        return self._board.copy()
    
    def get_legal_moves(self) -> List[chess.Move]:
        """Get list of legal moves in current position"""
        if not self._board:
            return []
        return list(self._board.legal_moves)
    
    def get_turn(self) -> bool:
        """Get current side to move (True for white, False for black)"""
        if not self._board:
            return True
        return self._board.turn

    def parse_square(self, square: str) -> chess.Square:
        """Parse a square from a string"""
        return chess.parse_square(square)
    
    def square_file(self, square: chess.Square) -> int:
        """Get the file index of a square"""
        return chess.square_file(square)
    
    def square_rank(self, square: chess.Square) -> int:
        """Get the rank index of a square"""
        return chess.square_rank(square)
