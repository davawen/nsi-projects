from turtle import *
from random import *
import sys

from enum import Enum
class Player(Enum):
    NONE = 0
    ONE = 1
    TWO = 2
    EITHER = 3
    
    def text(self):
        if self == Player.NONE:
            return "Aucun"
        elif self == Player.ONE:
            return 'J1'
        elif self == Player.TWO:
            return 'J2'
        elif self == Player.EITHER:
            return "Les deux"
    
    def sign(self):
        if self == Player.NONE:
            return ' '
        elif self == Player.ONE:
            return 'X'
        elif self == Player.TWO:
            return 'O'
        elif self == Player.EITHER:
            assert(false)
    
    def switch(self):
        return Player.TWO if self == Player.ONE else Player.ONE

def render(board):
    for j, row in enumerate(board):
        for i, c in enumerate(row):
            sys.stdout.write(f" {c.sign()}")
            if(i < 2):
                sys.stdout.write(" │")
        if(j < 2):
            sys.stdout.write("\n───┼───┼───")
        print()

def terrain():
    """créer l'interface graphique
    
    """
    WIDTH = 300
    HEIGHT=300
    screen = Screen()
    screen.setup(WIDTH + 20, HEIGHT+20)  # fudge factors due to window borders & title bar
    screen.setworldcoordinates(-10, -10, WIDTH+10, HEIGHT+10)
 

def premier_joueur():
    """Permet de trouver quel sera la premier jouer via l'aléatoire
    
    Returns
    -------
    string
        Renvoie le '1' ou '2' si un joueur à gagné. None sinon. 
    """
    return Player.ONE

def maj(x,y,joueur):
    """Mets a jouer l'interface graphique
    Parameters
    ----------
    x : int ou float
        Coordonnée de la ligne
    y : int ou float
        Coordonnée de la collones
    joueur : string
        Le joueur venant de jouer
    """
    color('red', 'red')
    begin_fill()
    penup()
    goto(75 ,250 -200  )
    pendown()
    circle(25,360)
    end_fill()

def gagnant(partie):
    """
        Renvoie le joueur qui a gagné, si il n'y en a aucun, ou si il y a égalité
    """
    def transpose(partie):
        return [list(x) for x in zip(*partie)]

    def line_equal(line):
        if line[0] == line[1] == line[2]:
            return line[0]
        return Player.NONE
    
    def is_full():
        for j in range(3):
            for i in range(3):
                if partie[j][i] == Player.NONE:
                    return False
        return True
    
    won = Player.NONE
    def set_won(value):
        nonlocal won
        if value != Player.NONE and won == Player.NONE:
            won = value
    
    for row in partie:
        set_won(line_equal(row))
    
    partie_cols = transpose(partie)
    for col in partie_cols:
        set_won(line_equal(col))
    
    partie_diags = [ [partie[i][i] for i in range(3)], [partie[2 - i][i] for i in range(3)] ]
    for diag in partie_diags:
        set_won(line_equal(diag))
    
    if(is_full()):
        set_won(Player.EITHER)
    
    return won


def morpion():
    """Permet de jouer au morpion.
    Permet la jeux d'une partie de morpion.
    
    Parameters
    ----------
    None

    Returns
    -------
    None    """
    #terrain()
    joueur = premier_joueur()
    cout = 0 
    partie = [ [Player.NONE for _ in range(3)] for _ in range(3) ]
    won = Player.NONE
    while(won == Player.NONE):
        print('Tour de', joueur.text())
        render(partie)
        
        valid = False
        while(not valid):
            x, y = int(input('Colonne: ')), int(input('Ligne: '))
            
            if partie[y][x] == Player.NONE:
                partie[y][x] = joueur
                valid = True
        
        won = gagnant(partie)
        joueur = joueur.switch()
        print()
    
    return won
       
if __name__ == '__main__':
    dict = {}
    for i in range(10):
        morpion()