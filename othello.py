import turtle as t
import sys
import cProfile
from time import sleep
from enum import Enum
from math import copysign, inf

SCREEN_SIZE = 800
MARGIN = 20
BOARD_SIZE = SCREEN_SIZE - MARGIN*2

TILE_NUM = 8
TILE_SIZE = BOARD_SIZE / TILE_NUM
CIRCLE_SIZE = TILE_SIZE / 2

class Stone(Enum):
    BLACK = 0
    WHITE = 1
    def inverse(self):
        return Stone.BLACK if self == Stone.WHITE else Stone.WHITE

def cartesian_product(w, h = None):
    """Creates an iterator over the 2d range [(0, 0); (w, h))"""
    if h == None:
        h = w

    for j in range(h):
        for i in range(w):
            yield (i, j)

class Board:
    def __init__(self, starting_stone):
        self.board = [[ None for _ in range(TILE_NUM) ] for _ in range(TILE_NUM)]
        self.num = { Stone.BLACK: 0, Stone.WHITE: 0 }
        # The stone of the currently playing player
        self.stone = starting_stone 
        # Set of all legal moves for the current stone, key has form (x, y)
        self.legal_moves = set()
        # Did the other player have any move to their disposition before this turn?
        self.last_could_move = True
    
    def copy(self):
        b = Board(self.stone)
        b.board = [[ self.board[j][i] for i in range(TILE_NUM) ] for j in range(TILE_NUM)]
        b.num = self.num.copy()
        b.legal_moves = self.legal_moves.copy()
        return b
    
    def set(self, stone, tx, ty):
        """Sets the given tile in the board to the given value, while keeping track of the number of different stones"""
        present = self.get(tx, ty)
        if present == None:
            self.num[stone] += 1
        else:
            self.num[stone] += 1
            self.num[present] -= 1
        self.board[ty][tx] = stone
        
    def get(self, tx, ty):
        return self.board[ty][tx]

    def switch_stone(self):
        """Switch the current player and regenerate the legal moves for the new one"""
        self.last_could_move = (len(self.legal_moves) != 0) 
        
        self.stone = self.stone.inverse()
        self.generate_legal_moves()
    
    def is_game_finished(self):
        """
        Checks if there aren't any new move possible on the board
        @returns False if the game is still going, the stone that won if one did, or None if there was a tie
        """
        # If either player can still move
        if self.last_could_move or len(self.legal_moves) != 0:
            return False
        
        if self.num[Stone.BLACK] > self.num[Stone.WHITE]:
            return Stone.BLACK
        elif self.num[Stone.BLACK] < self.num[Stone.WHITE]:
            return Stone.WHITE
        else:
            return None
    
    def tiles(self):
        """Creates an iterator over every tile on the board in the form (stone, tx, ty)"""
        for (i, j) in cartesian_product(TILE_NUM):
            yield (self.get(i, j), i, j)
    
    def in_bounds(self, tx, ty):
        return tx >= 0 and tx < TILE_NUM and ty >= 0 and ty < TILE_NUM

    def peek_dir(self, stone, tx, ty, dirx, diry):
        """
        Check if a tile is possible to play on in a certain direction
        @returns None if it isn't, or a (x, y) tuple of the first allied stone in that direction
        """
        if self.in_bounds(tx + dirx, ty + diry) and self.get(tx + dirx, ty + diry) == stone.inverse():
            x = tx + dirx
            y = ty + diry
            while(self.in_bounds(x, y)):
                if self.get(x, y) == stone:
                    return (x, y)
                elif self.get(x, y) == None:
                    return None
                x += dirx
                y += diry
        return None

    def is_legal(self, stone, tx, ty):
        """
        Returns True if the move is authorized by the game's rules, False if it isn't
        DONE: Switch every statement which expected this to return wether the move was `illegal`
        """
        if self.get(tx, ty) != None:
            return False
        
        for j in range(-1, 2):
            for i in range(-1, 2):
                if i == 0 and j == 0: # Skip this (center) tile
                    continue
                plug = self.peek_dir(stone, tx, ty, i, j)
                if plug != None:
                    return True
        return False
    
    def generate_legal_moves(self):
        self.legal_moves.clear()
        for j in range(TILE_NUM):
            for i in range(TILE_NUM):
                if self.is_legal(self.stone, i, j):
                    self.legal_moves.add((i, j))
                    
    def fill_dir(self, stone, tx, ty, dirx, diry, plugx, plugy):
        """
        Fills a line of stones from (tx, ty) to (plugx, plugy) with the given direction (dirx, diry).
        The coordinates should be aligned.
        dirx and diry shall either be 1, 0, or -1.
        """
        assert(dirx == 1 or dirx == 0 or dirx == -1)
        assert(diry == 1 or diry == 0 or diry == -1)

        x = tx + dirx
        if diry == 0:
            while(copysign(x, dirx) < copysign(plugx, dirx)): # Allow for iteration in both left and right
                self.set(stone, x, ty)
                x += dirx
        else: # Up/down and diagonals
            y = ty + diry
            while(copysign(y, diry) < copysign(plugy, diry)):
                self.set(stone, x, y)
                x += dirx
                y += diry
        self.set(stone, tx, ty)
    
    def place(self, tx, ty):
        """
        Places the current playing stone at a given position and applies every effect needed to the board
        @returns wether the move was applied (if it was in the legal moves)
        """
        if (tx, ty) not in self.legal_moves:
            return False
        
        for j in range(-1, 2):
            for i in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                plug = self.peek_dir(self.stone, tx, ty, i, j)
                if plug != None:
                    plugx, plugy = plug
                    self.fill_dir(self.stone, tx, ty, i, j, plugx, plugy)
        return True

class DecisionTree:
    MAX_DEPTH = 4
    def __init__(self, board_state, depth = 0):
        self.nodes = {}
        self.state = board_state
        if depth >= DecisionTree.MAX_DEPTH:
            self.empty = True
        else:
            self.empty = False
            self.generate_childs(depth)

    def generate_childs(self, depth):
        for (i, j) in cartesian_product(TILE_NUM):
            board = self.state.copy()
            legal = board.place(i, j)
            if legal:
                board.switch_stone()
                self.nodes[(i, j)] = DecisionTree(board, depth+1)
        copy_state = self.state.copy()
        copy_state.switch_stone()
        self.nodes[(-1, -1)] = DecisionTree(copy_state, depth+1) # = pass your turn

    def recalculate(self, depth = 0):
        if not self.empty:
            for (_, node) in self.nodes.items():
                node.recalculate(depth + 1)
        else:
            self.empty = False
            self.generate_childs(depth)

    def minimax(self, maximizing_stone):
        if self.empty:
            return self.state.num[maximizing_stone], []
        
        value = 0
        value_move = (-1, -1)
        next_moves = []
        if self.state.stone == maximizing_stone:
            value = -inf
            for move, node in self.nodes.items():
                minimax_value, minimax_next_moves = node.minimax(maximizing_stone)
                if value < minimax_value:
                    value = minimax_value
                    value_move = move
                    next_moves = minimax_next_moves
        else:
            value = inf
            for move, node in self.nodes.items():
                minimax_value, minimax_next_moves = node.minimax(maximizing_stone)
                if value > minimax_value:
                    value = minimax_value
                    value_move = move
                    next_moves = minimax_next_moves
        next_moves.append(value_move)
        return value, next_moves
    
    def dump(self, file, depth = 0):
        space = "    " * depth
        for (tx, ty), node in self.nodes:
            s = f"{space}Move: ({tx}, {ty}), Blacks: {node.state.num[Stone.BLACK]}, Whites: {node.state.num[Stone.WHITE]}, State:\n"
            for j in range(TILE_NUM):
                s += space
                for i in range(TILE_NUM):
                    t = node.state.get(i, j)
                    if t == None:
                        s += "` "
                    elif t == Stone.BLACK:
                        if i == tx and j == ty:
                            s += "b "
                        else:
                            s += "# "
                    else:
                        if i == tx and j == ty:
                            s += "w "
                        else:
                            s += "o "
                s += "\n"
            s += "\n"
            file.write(s)
            node.dump(file, depth + 1)

def build():
    """Creates the framework of the board at the start of the game"""
    t.setundobuffer(800)
    t.setup(SCREEN_SIZE, SCREEN_SIZE)
    t.setworldcoordinates(0, SCREEN_SIZE, SCREEN_SIZE, 0)
    t.hideturtle() # Hide cursor
    t.tracer(0, 0) # Disable screen refreshes
    t.pu()

    t.speed(0)
    t.goto(MARGIN, MARGIN)
    t.pd()
    for i in range(TILE_NUM + 1):
        ypos = i*TILE_SIZE + MARGIN
        t.pu()
        t.goto(MARGIN, ypos)
        t.pd()
        t.goto(MARGIN + BOARD_SIZE, ypos)
    for i in range(TILE_NUM + 1):
        xpos = i*TILE_SIZE + MARGIN
        t.pu()
        t.goto(xpos, MARGIN)
        t.pd()
        t.goto(xpos, MARGIN + BOARD_SIZE)
    t.pu()

def world_to_tile(x, y):
    if x < MARGIN or x > MARGIN + BOARD_SIZE or y < MARGIN or y > MARGIN + BOARD_SIZE:
        return -1, -1
    
    x, y = x - MARGIN, y - MARGIN
    x, y = x // TILE_SIZE, y // TILE_SIZE
    return int(x), int(y)

def tile_to_world(tx, ty):
    x, y = tx * TILE_SIZE, ty * TILE_SIZE
    x, y = x + MARGIN, y + MARGIN
    if tx == -1:
        x = -1
    if ty == -1:
        y = -1
    return x, y

board = Board(Stone.WHITE)
board.set(Stone.WHITE, 3, 3)
board.set(Stone.WHITE, 4, 4)
board.set(Stone.BLACK, 3, 4)
board.set(Stone.BLACK, 4, 3)
board.generate_legal_moves()

tree = DecisionTree(board.copy())
human_player = False

def click(x, y):
    tx, ty = world_to_tile(x, y)
    
    if tx != -1 and ty != -1:
        legal = board.place(tx, ty)
        if not legal:
            return
    board.switch_stone()
    draw_board()
    
    # In mode versus, next click would be the other player
    if not human_player:
        global tree
        tree = tree.nodes[(tx, ty)]
        tree.recalculate() # Regenerate the last layer of the tree

        value, next_moves = tree.minimax(Stone.BLACK)
        tx, ty = next_moves[-1]
        if tx != -1 and ty != -1:
            board.place(tx, ty) 
        board.switch_stone()
        draw_board()

        tree = tree.nodes[(tx, ty)] # Move the tree to my move (but no need to recalculate as long as MAX_DEPTH is > than 1)
    
    end = board.is_game_finished()
    if end != False:
        if end == Stone.BLACK:
            text = "Gagnant: joueur noir"
        elif end == Stone.WHITE:
            text = "Gagnant: joueur blanc"
        else:
            text = "Pas de gagnant: égalité!"
        t.goto(SCREEN_SIZE/2, 20)
        t.pd()
        t.color("black")
        t.write(text, align="center", font=("Arial", 20, "normal"))
        sleep(4)
        t.bye()
        
def draw_board():
    def black_circle(size):
        t.pd()
        t.dot(size)
        t.pu()

    def white_circle(size):
        t.pd()
        t.dot(size)
        t.dot(size - 2, "white")
        t.pu()

    def stone_circle(stone, size):
        if stone == Stone.BLACK:
            black_circle(size)
        elif stone == Stone.WHITE:
            white_circle(size)
    
    def tile_coordinate(i, j):
        t.pd()
        t.write(f"({i}, {j})", align="center")
        t.pu()
    
    t.pu()
    for (stone, i, j) in board.tiles():
            x, y = tile_to_world(i, j)
            t.goto(x + TILE_SIZE/2, y + TILE_SIZE/2)
            if stone != None: # Draw every placed stone
                stone_circle(stone, CIRCLE_SIZE)
            elif (i, j) in board.legal_moves: # Draw every legal move possible
                stone_circle(board.stone, 7)
            else:
                t.pd()
                t.dot(CIRCLE_SIZE, "white") # Clear cell
                t.pu()
                
    t.goto(10, 10)
    stone_circle(board.stone, 5)
    
    t.pu()
    t.update()

def main():
    # Pass game mode as command line argument
    if len(sys.argv) >= 2:
        if sys.argv[1] == "versus":
            global human_player
            human_player = True
    
    build()
    draw_board()
    
    ws = t.Screen()
    ws.onclick(click)
    ws.mainloop()

if __name__ == "__main__":
    main()
