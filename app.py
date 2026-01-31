from flask import Flask, request, jsonify, render_template_string
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
DIFFICULTY_DEPTH = {1: 1, 2: 2, 3: 3}

gameSettings = {}

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Chess Game</title>
  <style>
    body { font-family: Arial; background:#f0f0f0; display:flex; justify-content:center; padding:20px; }
    .container { display:flex; flex-direction:column; align-items:center; }
    .player-info { display:flex; justify-content:space-between; width:480px; margin:10px 0; font-size:18px; }
    .board { display:grid; grid-template-columns:repeat(8,60px); grid-template-rows:repeat(8,60px); border:2px solid #333; }
    .square { width:60px; height:60px; display:flex; align-items:center; justify-content:center; font-size:32px; cursor:pointer; }
    .light { background:#eee; } .dark { background:#999; }
    .square.selected { outline:3px solid yellow; } .square.highlight { background-color:rgba(0,255,0,0.3); }
    .sidebar { width:150px; margin-left:20px; background:#fff; border:1px solid #333; padding:10px; height:400px; overflow-y:auto; }
    .menu { margin-top:20px; }
    .popup { position:fixed; top:20%; left:35%; background:white; padding:20px; border:2px solid #333; z-index:10; width:300px; box-shadow:0 0 10px rgba(0,0,0,0.3); }
  </style>
</head>
<body>
  <div id="start-popup" class="popup">
    <h2>Start New Game</h2>
    <label>Game Mode:
      <select id="game-mode"><option value="ai">AI vs Player</option><option value="pvp">Player vs Player</option></select>
    </label>
    <label>Board Side:
      <select id="board-side"><option value="white">White</option><option value="black">Black</option></select>
    </label>
    <label>Player 1 Name: <input type="text" id="player1-name"/></label>
    <label id="player2-label">Player 2 Name: <input type="text" id="player2-name"/></label>
    <label>Time Control:
      <select id="time-control"><option value="600">10 minutes</option><option value="300">5 minutes</option></select>
    </label>
    <div id="difficulty-section">
      <label>Difficulty:
        <select id="difficulty"><option value="1">Easy</option><option value="2">Medium</option><option value="3">Hard</option></select>
      </label>
    </div>
    <button onclick="startGame()">Start Game</button>
  </div>

  <div class="container">
    <div class="player-info top">
      <div class="avatar">👤</div><div class="name" id="white-name">White</div><div class="timer" id="white-timer">10:00</div>
    </div>
    <div class="board" id="chess-board"></div>
    <div class="player-info bottom">
      <div class="avatar">👤</div><div class="name" id="black-name">Black</div><div class="timer" id="black-timer">10:00</div>
    </div>
  </div>

  <div class="sidebar"><h3>Move History</h3><ol id="move-history"></ol></div>

  <div class="menu">
    <button onclick="undoMove()">Undo</button>
    <button onclick="resetGame()">Reset</button>
    <button onclick="offerDraw()">Draw</button>
    <button onclick="resign()">Resign</button>
  </div>

  <div id="end-popup" class="popup" style="display:none;">
    <h2 id="winner-text"></h2>
    <button onclick="resetGame()">Play Again</button>
    <button onclick="exitGame()">Exit</button>
  </div>

<script>
const PIECE_SYMBOLS = {'P':'♙','R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','p':'♟','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚'};
let selectedSquare=null, gameSettings={}, whiteTime, blackTime, timerInterval, currentTurn='w';

function renderBoard(fen){
  const boardEl=document.getElementById('chess-board'); boardEl.innerHTML='';
  const rows=fen.split(' ')[0].split('/');
  rows.forEach((row,i)=>{let col=0;for(const char of row){if(isNaN(char)){const sq=document.createElement('div');sq.className=`square ${(i+col)%2===0?'light':'dark'}`;sq.textContent=PIECE_SYMBOLS[char]||'';sq.dataset.square=`${String.fromCharCode(97+col)}${8-i}`;sq.onclick=()=>selectSquare(sq.dataset.square);boardEl.appendChild(sq);col++;}else{for(let j=0;j<parseInt(char);j++){const sq=document.createElement('div');sq.className=`square ${(i+col)%2===0?'light':'dark'}`;sq.dataset.square=`${String.fromCharCode(97+col)}${8-i}`;sq.onclick=()=>selectSquare(sq.dataset.square);boardEl.appendChild(sq);col++;}}}});}

function selectSquare(square){clearHighlights();const sqEl=document.querySelector(`[data-square='${square}']`);sqEl.classList.add('selected');if(selectedSquare){const move=selectedSquare+square;fetch('/move',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({move})}).then(res=>res.json()).then(data=>{if(data.status==='ok'){renderBoard(data.fen);updateMoveHistory(data.move);checkStatus(data.fen);switchTurn();if(gameSettings.mode==='ai' && currentTurn==='b'){aiMove();}}});selectedSquare=null;}else{selectedSquare=square;}}

function clearHighlights(){document.querySelectorAll('.square').forEach(sq=>sq.classList.remove('selected','highlight'));}
function updateMoveHistory(move){const li=document.createElement('li');li.textContent=move;document.getElementById('move-history').appendChild(li);}
function startGame(){const mode=document.getElementById('game-mode').value;const player1=document.getElementById('player1-name').value||"White";const player2=document.getElementById('player2-name').value||"Black";const difficulty=parseInt(document.getElementById('difficulty').value);const baseTime=parseInt(document.getElementById('time-control').value);gameSettings={mode,difficulty,baseTime,player1,player2};fetch('/start_game',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(gameSettings)});document.getElementById('start-popup').style.display='none';document.getElementById('white-name').textContent=player1;document.getElementById('black-name').textContent=player2;whiteTime=baseTime;blackTime=baseTime;updateTimers();currentTurn='w';renderBoard('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');}
function updateTimers(){document.getElementById('white-timer').textContent=formatTime(whiteTime);document.getElementById('black-timer').textContent=formatTime(blackTime);}
function formatTime(seconds){const min=Math.floor(seconds/60);const sec=seconds%60;return `${min}:${sec.toString().padStart(2,'0')}`;}
function switchTurn(){currentTurn=currentTurn==='w'?'b':'w';}
function checkStatus(fen){if(fen.includes('#')){showEnd('Checkmate!');}}
function showEnd(text){document.getElementById('winner-text').textContent=text;document.getElementById('end-popup').style.display='block';}
function aiMove(){fetch('/ai_move').then(res=>res.json()).then(data=>{renderBoard(data.fen);updateMoveHistory(data.move);checkStatus(data.fen);switchTurn();});}
function undoMove(){alert('Undo not implemented');}
function resetGame(){location.reload();}
function offerDraw(){alert('Draw offered');}
function resign(){alert('Resigned');}
function exitGame(){window.close();}
</script>
</body>
</html>
""")

@app.route('/start_game', methods=['POST'])
def start_game():
    global gameSettings
    gameSettings = request.get_json()
    global board
    board = chess.Board()
    return jsonify({'status': 'ok'})

@app.route('/move', methods=['POST'])
def make_move():
    data = request.get_json()
    move_str = data['move']
    try:
        move = chess.Move.from_uci(move_str)
        if move in board.legal_moves:
            board.push(move)
            return jsonify({'status': 'ok', 'fen': board.fen(), 'move': move_str})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid move'})
    except:
        return jsonify({'status': 'error', 'message': 'Invalid move format'})

@app.route('/ai_move')
def ai_move():
    if board.is_game_over():
        return jsonify({'fen': board.fen(), 'move': None})
    depth = DIFFICULTY_DEPTH.get(gameSettings.get('difficulty', 1), 1)
    _, best_move = minimax(board, depth, float('-inf'), float('inf'), board.turn)
    if best_move:
        board.push(best_move)
        return jsonify({'fen': board.fen(), 'move': str(best_move)})
    return jsonify({'fen': board.fen(), 'move': None})

if __name__ == '__main__':
    app.run(debug=True)