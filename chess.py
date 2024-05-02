from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from abc import ABC, abstractmethod
import sqlite3
import uvicorn

conn = sqlite3.connect('results.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS matches
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   player1 TEXT,
                   player2 TEXT,
                   winner TEXT,
                   timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')


def save_match_result(player1, player2, winner):
    cursor.execute('''INSERT INTO matches (player1, player2, winner) VALUES (?, ?, ?)''', (player1, player2, winner))
    conn.commit()


def close_db_connection():
    conn.close()


app = FastAPI()
game = None


class Piece(ABC):
    def __init__(self, color):
        self.color = color

    @abstractmethod
    def validate_move(self, start, end):
        pass

    @abstractmethod
    def make_move(self, start, end):
        pass


class Pawn(Piece):
    def validate_move(self, start, end):
        if start[0] == end[0] and start[1] == end[1]:
            return False
        return True

    def make_move(self, start, end):
        pass


class Rook(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Knight(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Bishop(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Queen(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class King(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Board:
    def __init__(self):
        self.board = [
            [Rook("black"), Knight("black"), Bishop("black"), Queen("black"), King("black"), Bishop("black"),
             Knight("black"), Rook("black")],
            [Pawn("black"), Pawn("black"), Pawn("black"), Pawn("black"), Pawn("black"), Pawn("black"),
             Pawn("black"), Pawn("black")],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [Pawn("white"), Pawn("white"), Pawn("white"), Pawn("white"), Pawn("white"), Pawn("white"), Pawn("white"),
             Pawn("white")],
            [Rook("white"), Knight("white"), Bishop("white"), Queen("white"), King("white"), Bishop("white"),
             Knight("white"), Rook("white")]
        ]

        self.coordinates = []
        for row_num in range(8):
            for col_num in range(8):
                col_letter = chr(col_num + ord('a'))
                self.coordinates.append(f"{col_letter}{row_num}")

    def display_board(self):
        for row in self.board:
            print(row)

    def get_piece_at_position(self, position):
        row, col = int(position[1]), ord(position[0]) - ord('a')
        return self.board[row][col]


board = Board()
board.display_board()


class Game:
    def __init__(self):
        self.board = Board()
        self.history = []
        self.current_player = "player1"

    def move(self, player, piece, start, end):
        if not self.validate_move(player, piece, start, end):
            raise HTTPException(status_code=400, detail="Wrong move")

        start_index = self.board.coordinates.index(start)
        end_index = self.board.coordinates.index(end)

        if self.board.board[end_index // 8][end_index % 8] is not None:
            raise HTTPException(status_code=400, detail="Cell is already taken")

        piece.make_move(start, end)
        self.history.append((player, piece, start, end))
        self.switch_player()

        if self.check_pawns_eaten():
            self.end_game()

        print(f"Piece on the cell {start} was moved to {end}")

    def switch_player(self):
        self.current_player = "player2" if self.current_player == "player1" else "player1"

    def validate_move(self, player, piece, start, end):
        end_index = self.board.coordinates.index(end)
        if self.board.board[end_index // 8][end_index % 8] is not None:
            return False
        return piece.validate_move(start, end)

    def check_pawns_eaten(self):
        pawns_color = "white" if self.current_player == "player1" else "black"
        pawns_row = 6 if pawns_color == "white" else 1
        for piece in self.board.board[pawns_row]:
            if isinstance(piece, Pawn) and piece.color == pawns_color:
                return False
        return True

    def end_game(self):
        winner = "player1" if self.current_player == "player2" else "player2"
        save_match_result("Opponent", "Opponent", winner)
        raise HTTPException(status_code=200, detail=f"Player {winner} won!")



@app.post("/Game start")
async def start_game(player1: str, player2: str, player_number_1: str, player_number_2: str):
    global game
    game = Game()
    game.current_player = player1

    if player_number_1 == "white":
        game.board.board[6] = [Pawn("white") for _ in range(8)]
    else:
        game.board.board[1] = [Pawn("black") for _ in range(8)]

    if player_number_2 == "black":
        game.board.board[0] = [
            Rook("black"), Knight("black"), Bishop("black"), Queen("black"), King("black"),
            Bishop("black"), Knight("black"), Rook("black")
        ]
    else:
        game.board.board[7] = [
            Rook("white"), Knight("white"), Bishop("white"), Queen("white"), King("white"),
            Bishop("white"), Knight("white"), Rook("white")
        ]

    return {"message": "Game successfully started", "player1": player1, "player2": player2}


@app.post("/Pawn move", response_class=HTMLResponse)
async def move(player: str, start: str, end: str):
    if game is None:
        raise HTTPException(status_code=400, detail="Game has not been started yet.")

    start_index = game.board.coordinates.index(start)
    piece = game.board.get_piece_at_position(start)

    if piece is None:
        raise HTTPException(status_code=400, detail="Cell is empty")

    if (game.current_player == "player1" and "white" not in piece) or (
            game.current_player == "player2" and "black" not in piece):
        raise HTTPException(status_code=400, detail="Not your piece")

    if isinstance(piece, str) and "pawn" in piece.lower():
        piece_instance = Pawn(piece)
    elif isinstance(piece, str) and "rook" in piece.lower():
        piece_instance = Rook(piece)
    elif isinstance(piece, str) and "king" in piece.lower():
        piece_instance = Knight(piece)
    else:
        piece_instance = piece

    if piece_instance is None:
        raise HTTPException(status_code=400, detail="Wrong move")
    game.move(player, piece_instance, start, end)
    end_index = game.board.coordinates.index(end)
    if isinstance(piece, str) and "pawn" in piece.lower() and game.board.board[end_index // 8][end_index % 8] is not None:
        game.board.board[end_index // 8][end_index % 8] = None
    return await get_piece_list()

@app.get("/board", response_class=HTMLResponse) # only for visuals
async def get_piece_list():
    if game is None or game.board is None or game.board.board is None:
        return HTMLResponse(content="Game has not started yet.")
    board_html = "<table border='1' cellpadding='20'>"
    for row_num in range(7, -1, -1):
        board_html += f"<tr><td style='background-color: white; color: black; font-size: 24px;'>{row_num + 1}</td>"
        for col_num in range(8):
            piece = game.board.board[row_num][col_num]
            if piece is not None:
                piece_type = piece.__class__.__name__.lower()
                piece_color = piece.color
                text_color = "white" if piece_color == "black" else "black"
                background_color = "black" if piece_color == "black" else "white"
                board_html += f"<td style='background-color: {background_color}; color: {text_color}; font-size: 24px;'>{piece_type} ({piece_color})</td>"
            else:
                if (row_num + col_num) % 2 == 0:
                    board_html += "<td style='background-color: white;'></td>"
                else:
                    board_html += "<td style='background-color: white;'></td>"
        board_html += "</tr>"
    board_html += "<tr>"
    board_html += "<td></td>"
    for col_char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
        board_html += f"<td style='background-color: white; color: black; font-size: 24px;'>{col_char}</td>"
    board_html += "</tr>"
    board_html += "<tr><td colspan='9'></td></tr>"
    board_html += "</table>"
    return HTMLResponse(content=board_html)


@app.get("/result", response_class=HTMLResponse)
async def get_match_results():
    conn = sqlite3.connect('results.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches")
    results = cursor.fetchall()
    conn.close()

    table_content = "<h2>Game results</h2><table border='1'><tr><th>ID</th><th>Player 1</th><th>Player 2</th><th>Winner</th><th>Time</th></tr>"
    for row in results:
        table_content += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
    table_content += "</table>"
    return HTMLResponse(content=table_content)


@app.post("/fast_win", response_class=HTMLResponse)
async def test_win(winner_name: str):
    if game is None:
        raise HTTPException(status_code=400, detail="Game has not been started")

    save_match_result(game.current_player, "Loser", winner_name)
    return HTMLResponse(content=f"Winner {winner_name}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)