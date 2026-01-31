import tkinter as tk
from tkinter import messagebox
import chess

SQUARE_SIZE = 80

PIECE_SYMBOLS = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
}

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess – Player vs Bot (AIML)")
        self.board = chess.Board()
        self.selected_square = None
        self.depth = 2

        self.canvas = tk.Canvas(root, width=640, height=640)
        self.canvas.grid(row=0, column=0, columnspan=4)

        self.status = tk.Label(root, text="Your Turn (White)", font=("Arial", 12))
        self.status.grid(row=1, column=0, columnspan=4)

        tk.Button(root, text="Restart", command=self.restart).grid(row=2, column=0)
        tk.Button(root, text="Undo", command=self.undo).grid(row=2, column=1)
        tk.Button(root, text="Easy", command=lambda: self.set_depth(1)).grid(row=2, column=2)
        tk.Button(root, text="Medium", command=lambda: self.set_depth(2)).grid(row=2, column=3)
        tk.Button(root, text="Hard", command=lambda: self.set_depth(3)).grid(row=3, column=1, columnspan=2)

        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()

    def set_depth(self, d):
        self.depth = d
        messagebox.showinfo("Difficulty", f"Difficulty set to {['Easy','Medium','Hard'][d-1]}")

    def restart(self):
        self.board.reset()
        self.selected_square = None
        self.status.config(text="Game Restarted – Your Turn")
        self.draw_board()

    def undo(self):
        if len(self.board.move_stack) >= 2:
            self.board.pop()
            self.board.pop()
            self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                color = "#EEEED2" if (r + c) % 2 == 0 else "#769656"
                self.canvas.create_rectangle(
                    c*SQUARE_SIZE, r*SQUARE_SIZE,
                    (c+1)*SQUARE_SIZE, (r+1)*SQUARE_SIZE,
                    fill=color
                )

        if self.selected_square is not None:
            r = 7 - chess.square_rank(self.selected_square)
            c = chess.square_file(self.selected_square)
            self.canvas.create_rectangle(
                c*SQUARE_SIZE, r*SQUARE_SIZE,
                (c+1)*SQUARE_SIZE, (r+1)*SQUARE_SIZE,
                outline="red", width=4
            )

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                r = 7 - chess.square_rank(square)
                c = chess.square_file(square)
                self.canvas.create_text(
                    c*SQUARE_SIZE+40, r*SQUARE_SIZE+40,
                    text=PIECE_SYMBOLS[piece.symbol()],
                    font=("Arial", 42)
                )

    def on_click(self, event):
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        square = chess.square(col, 7-row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if self.board.piece_at(self.selected_square).piece_type == chess.PAWN and chess.square_rank(square) == 7:
                move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.draw_board()
                self.status.config(text="Bot Thinking...")
                self.root.after(300, self.bot_move)
            else:
                self.selected_square = None

        self.draw_board()

    def evaluate(self):
        score = 0
        for p in PIECE_VALUES:
            score += len(self.board.pieces(p, chess.WHITE)) * PIECE_VALUES[p]
            score -= len(self.board.pieces(p, chess.BLACK)) * PIECE_VALUES[p]
        return score

    def minimax(self, depth, maximizing):
        if depth == 0 or self.board.is_game_over():
            return self.evaluate()

        if maximizing:
            best = -9999
            for m in self.board.legal_moves:
                self.board.push(m)
                best = max(best, self.minimax(depth-1, False))
                self.board.pop()
            return best
        else:
            best = 9999
            for m in self.board.legal_moves:
                self.board.push(m)
                best = min(best, self.minimax(depth-1, True))
                self.board.pop()
            return best

    def bot_move(self):
        if self.board.is_game_over():
            messagebox.showinfo("Game Over", self.board.result())
            return

        best_move = None
        best_score = 9999

        for move in self.board.legal_moves:
            self.board.push(move)
            score = self.minimax(self.depth, True)
            self.board.pop()

            if score < best_score:
                best_score = score
                best_move = move

        self.board.push(best_move)
        self.status.config(text="Your Turn")
        self.draw_board()

def main():
    root = tk.Tk()
    ChessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
