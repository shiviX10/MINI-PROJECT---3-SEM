import tkinter as tk
from tkinter import messagebox
import chess

SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * 8

# Colors inspired by chess.com
LIGHT = "#f0d9b5"
DARK = "#b58863"
HIGHLIGHT = "#f7ec6e"            # Last move highlight border
LEGAL_MOVE_HIGHLIGHT = "#6fc3df"  # Legal moves circle
HOVER = "#c7e0f4"
DARK_BG = "#2b2b2b"
LIGHT_BG = "#f5f5f5"

PIECE_SYMBOLS = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
}

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess – AIML Project")
        self.root.geometry("1200x900")
        self.root.configure(bg=LIGHT_BG)

        # Game state
        self.board = chess.Board()
        self.selected_square = None
        self.last_move = None
        self.legal_moves = []
        self.depth = 3
        self.pvp_mode = False
        self.dark_mode = False
        self.white_time = 300
        self.black_time = 300
        self.timer_running = False

        # Player names
        self.white_name = tk.StringVar(value="White Player")
        self.black_name = tk.StringVar(value="Black Player")

        self.show_startup_frame()

    # ---------------- STARTUP FRAME ----------------
    def show_startup_frame(self):
        self.startup_frame = tk.Frame(self.root, bg=LIGHT_BG)
        self.startup_frame.pack(fill="both", expand=True)

        tk.Label(self.startup_frame, text="Select Game Mode:", font=("Arial", 14, "bold"), bg=LIGHT_BG).pack(pady=10)
        self.mode_var = tk.StringVar(value="PvP")
        tk.Radiobutton(self.startup_frame, text="Player vs Player", variable=self.mode_var, value="PvP", bg=LIGHT_BG, font=("Arial",12), command=self.toggle_black_entry).pack(anchor="w", padx=20)
        tk.Radiobutton(self.startup_frame, text="AI-Bot vs Player", variable=self.mode_var, value="AI", bg=LIGHT_BG, font=("Arial",12), command=self.toggle_black_entry).pack(anchor="w", padx=20)

        tk.Label(self.startup_frame, text="Enter Player Names:", font=("Arial", 14, "bold"), bg=LIGHT_BG).pack(pady=10)
        self.white_entry_start = tk.Entry(self.startup_frame, textvariable=self.white_name, font=("Arial", 12))
        self.white_entry_start.pack(pady=5)
        self.black_entry_start = tk.Entry(self.startup_frame, textvariable=self.black_name, font=("Arial", 12))
        self.black_entry_start.pack(pady=5)

        tk.Button(self.startup_frame, text="Start Game", font=("Arial", 12), bg="#4CAF50", fg="white", command=self.start_game).pack(pady=20)

    def toggle_black_entry(self):
        if self.mode_var.get() == "AI":
            self.black_entry_start.pack_forget()
        else:
            self.black_entry_start.pack(pady=5)

    def start_game(self):
        self.pvp_mode = self.mode_var.get() == "PvP"
        self.startup_frame.destroy()
        self.setup_ui()
        self.draw_board()
        if self.pvp_mode:
            self.timer_running = True
            self.update_timer()

    # ---------------- UI ----------------
    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=LIGHT_BG)
        self.main_frame.pack(fill="both", expand=True)

        # Left panel: Player info + timers
        self.left_panel = tk.Frame(self.main_frame, bg=LIGHT_BG)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)
        tk.Label(self.left_panel, text="White", font=("Arial", 12, "bold"), bg=LIGHT_BG).pack(pady=5)
        tk.Entry(self.left_panel, textvariable=self.white_name, font=("Arial",12), width=15).pack()
        tk.Label(self.left_panel, text="Black", font=("Arial", 12, "bold"), bg=LIGHT_BG).pack(pady=5)
        tk.Entry(self.left_panel, textvariable=self.black_name, font=("Arial",12), width=15).pack()

        self.white_timer_label = tk.Label(self.left_panel, text="05:00", font=("Arial",14,"bold"), bg=LIGHT_BG, fg="#333")
        self.white_timer_label.pack(pady=10)
        self.black_timer_label = tk.Label(self.left_panel, text="05:00", font=("Arial",14,"bold"), bg=LIGHT_BG, fg="#333")
        self.black_timer_label.pack(pady=10)

        # Center panel: Board + status
        self.center_frame = tk.Frame(self.main_frame, bg=LIGHT_BG)
        self.center_frame.pack(side="left", padx=10)

        self.status = tk.Label(self.center_frame, text="Your Turn (White)", font=("Arial", 14, "bold"), bg=LIGHT_BG, fg="#222")
        self.status.pack(pady=5)

        self.board_frame = tk.Frame(self.center_frame, bd=4, relief="solid", bg=LIGHT_BG)
        self.board_frame.pack()
        self.canvas = tk.Canvas(self.board_frame, width=BOARD_SIZE, height=BOARD_SIZE, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)
        self.hover_square = None

        # Right panel: Move history
        self.history_frame = tk.Frame(self.main_frame, bg=LIGHT_BG)
        self.history_frame.pack(side="left", padx=10, pady=10, fill="y")
        tk.Label(self.history_frame, text="Move History", font=("Arial", 14, "bold"), bg=LIGHT_BG).pack(pady=5)
        self.move_history = tk.Text(self.history_frame, width=25, height=30, state="disabled", font=("Courier", 12))
        self.move_history.pack()

        # Top menu buttons
        self.menu_frame = tk.Frame(self.root, bg=LIGHT_BG)
        self.menu_frame.pack(pady=5)
        tk.Button(self.menu_frame, text="PvP Mode", font=("Arial",12), bg="#2196F3", fg="white", command=self.toggle_pvp).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Dark Mode", font=("Arial",12), bg="#FF9800", fg="white", command=self.toggle_dark).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Undo", font=("Arial",12), bg="#9C27B0", fg="white", command=self.undo).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Reset", font=("Arial",12), bg="#f44336", fg="white", command=self.restart).pack(side="left", padx=5)

    # ---------------- BOARD ----------------
    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7-r)
                color = LIGHT if (r+c)%2==0 else DARK
                if self.dark_mode:
                    color = "#3a3a3a" if (r+c)%2==0 else "#1f1f1f"

                x1, y1 = c*SQUARE_SIZE, r*SQUARE_SIZE
                x2, y2 = (c+1)*SQUARE_SIZE, (r+1)*SQUARE_SIZE

                # Draw square base
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Last move highlight (border)
                if self.last_move and (sq == self.last_move.from_square or sq == self.last_move.to_square):
                    self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, outline=HIGHLIGHT, width=4)

                # Legal moves (circle)
                if sq in self.legal_moves:
                    self.canvas.create_oval(x1+SQUARE_SIZE*0.35, y1+SQUARE_SIZE*0.35, x2-SQUARE_SIZE*0.35, y2-SQUARE_SIZE*0.35, fill=LEGAL_MOVE_HIGHLIGHT)

                # Hover effect
                if self.hover_square == sq:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=HOVER, outline="")

        # Draw pieces
        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if p:
                r = 7 - chess.square_rank(sq)
                c = chess.square_file(sq)
                piece_color = "#f0f0f0" if p.color == chess.WHITE else "#222222"
                self.canvas.create_text(c*SQUARE_SIZE+SQUARE_SIZE//2, r*SQUARE_SIZE+SQUARE_SIZE//2, text=PIECE_SYMBOLS[p.symbol()], font=("Arial",46,"bold"), fill=piece_color)

    # ---------------- EVENT HANDLERS ----------------
    def on_click(self, e):
        c, r = e.x // SQUARE_SIZE, e.y // SQUARE_SIZE
        sq = chess.square(c, 7-r)

        if self.selected_square is None:
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn:
                self.selected_square = sq
                self.legal_moves = [m.to_square for m in self.board.legal_moves if m.from_square == sq]
        else:
            move = chess.Move(self.selected_square, sq)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.last_move = move
                self.update_history(move)
                self.selected_square = None
                self.legal_moves = []
                self.draw_board()
                if not self.pvp_mode:
                    self.root.after(100, self.bot_move)
            else:
                self.selected_square = None
                self.legal_moves = []
        self.draw_board()

    def on_hover(self, e):
        c, r = e.x // SQUARE_SIZE, e.y // SQUARE_SIZE
        sq = chess.square(c, 7-r)
        if sq != self.hover_square:
            self.hover_square = sq
            self.draw_board()

    # ---------------- MOVE HISTORY ----------------
    def update_history(self, move):
        self.move_history.config(state="normal")
        self.move_history.insert("end", f"{self.board.fullmove_number}. {self.board.san(move)}\n")
        self.move_history.see("end")
        self.move_history.config(state="disabled")

    # ---------------- MODES ----------------
    def toggle_pvp(self):
        self.pvp_mode = not self.pvp_mode
        self.restart()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        bg = DARK_BG if self.dark_mode else LIGHT_BG
        self.root.configure(bg=bg)
        self.main_frame.configure(bg=bg)
        self.left_panel.configure(bg=bg)
        self.center_frame.configure(bg=bg)
        self.history_frame.configure(bg=bg)
        self.status.configure(bg=bg)
        self.white_timer_label.configure(bg=bg)
        self.black_timer_label.configure(bg=bg)
        self.menu_frame.configure(bg=bg)
        self.draw_board()

    # ---------------- TIMER ----------------
    def update_timer(self):
        if not self.timer_running or not self.pvp_mode:
            return
        if self.board.turn == chess.WHITE:
            self.white_time -= 1
        else:
            self.black_time -= 1
        self.white_timer_label.config(text=f"{self.white_time//60:02}:{self.white_time%60:02}")
        self.black_timer_label.config(text=f"{self.black_time//60:02}:{self.black_time%60:02}")
        if self.white_time <= 0 or self.black_time <= 0:
            messagebox.showinfo("Time Over", "Game Over")
            self.timer_running = False
            return
        self.root.after(1000, self.update_timer)

    # ---------------- GAME ----------------
    def restart(self):
        self.board.reset()
        self.selected_square = None
        self.last_move = None
        self.legal_moves = []
        self.white_time = 300
        self.black_time = 300
        self.timer_running = self.pvp_mode
        self.move_history.config(state="normal")
        self.move_history.delete('1.0', 'end')
        self.move_history.config(state="disabled")
        self.update_timer()
        self.draw_board()

    def undo(self):
        if len(self.board.move_stack) >= 1:
            self.board.pop()
            if not self.pvp_mode and len(self.board.move_stack):
                self.board.pop()
        self.last_move = self.board.move_stack[-1] if self.board.move_stack else None
        self.draw_board()

    # ---------------- AI ----------------
    def evaluate(self):
        score = 0
        for p in PIECE_VALUES:
            score += len(self.board.pieces(p, chess.WHITE)) * PIECE_VALUES[p]
            score -= len(self.board.pieces(p, chess.BLACK)) * PIECE_VALUES[p]
        return score

    def alphabeta(self, depth, alpha, beta, maximizing):
        if depth == 0 or self.board.is_game_over():
            return self.evaluate()
        moves = sorted(self.board.legal_moves, key=lambda m: self.board.is_capture(m), reverse=True)
        if maximizing:
            value = -99999
            for m in moves:
                self.board.push(m)
                value = max(value, self.alphabeta(depth-1, alpha, beta, False))
                self.board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 99999
            for m in moves:
                self.board.push(m)
                value = min(value, self.alphabeta(depth-1, alpha, beta, True))
                self.board.pop()
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    def bot_move(self):
        best_score = 99999
        best_move = None
        for move in self.board.legal_moves:
            self.board.push(move)
            score = self.alphabeta(self.depth, -100000, 100000, True)
            self.board.pop()
            if score < best_score:
                best_score = score
                best_move = move
        if best_move:
            self.board.push(best_move)
            self.last_move = best_move
            self.update_history(best_move)
            self.draw_board()


def main():
    root = tk.Tk()
    ChessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
