from flask import Flask, request, jsonify
import chess

app = Flask(__name__)
board = chess.Board()

# Piece values for evaluation
PIECE_VALUES = {
    'p': -1,'n': -3,'b': -3,'r': -5,'q': -9,'k': -1000,
    'P': 1,'N': 3,'B': 3,'R': 5,'Q': 9,'K': 1000
}

def evaluate_board(board):
    """Simple evaluation based on material balance."""
    return sum(PIECE_VALUES.get(str(piece), 0) for piece in board.piece_map().values())

def minimax(board, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None
    if maximizing:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth-1, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth-1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

# Difficulty levels mapped to depth
DIFFICULTY_DEPTH = {
    1: 1,   # Easy
    2: 2,   # Medium
    3: 3    # Hard
}

@app.route('/move', methods=['POST'])
def make_move():
    """Player makes a move in UCI format (e.g., 'e2e4')."""
    move = request.json['move']
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move in board.legal_moves:
            board.push(chess_move)
            return jsonify({'status': 'ok', 'fen': board.fen(), 'move': move})
        else:
            return jsonify({'status': 'invalid'})
    except Exception:
        return jsonify({'status': 'invalid'})

@app.route('/ai-move', methods=['POST'])
def ai_move():
    """AI makes a move using minimax with difficulty depth."""
    difficulty = int(request.json.get('difficulty', 2))  # default Medium
    depth = DIFFICULTY_DEPTH.get(difficulty, 2)
    maximizing = board.turn
    _, move = minimax(board, depth, float('-inf'), float('inf'), maximizing)
    if move:
        board.push(move)
        return jsonify({'status': 'ok', 'move': board.uci(move), 'fen': board.fen()})
    return jsonify({'status': 'no-move'})

@app.route('/undo', methods=['GET'])
def undo():
    """Undo last move."""
    if board.move_stack:
        board.pop()
    return jsonify({'fen': board.fen()})

@app.route('/reset', methods=['GET'])
def reset():
    """Reset the board."""
    global board
    board = chess.Board()
    return jsonify({'fen': board.fen()})

@app.route('/status', methods=['POST'])
def status():
    """Check game status (check, checkmate, winner)."""
    fen = request.json['fen']
    board.set_fen(fen)
    return jsonify({
        'check': board.is_check(),
        'checkmate': board.is_checkmate(),
        'winner': 'White' if board.result() == '1-0' else 'Black' if board.result() == '0-1' else None
    })

if __name__ == '__main__':
    app.run(debug=True)
