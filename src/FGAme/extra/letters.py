#-*- coding: utf8 -*-
from __future__ import absolute_import
if __name__ == '__main__':
    __package__ = 'FGAme.objects'; import FGAme.objects

from math import sqrt
from .poly import Poly, get_collision

class Letter(Poly):
    LETTERS = {
        '0': [(0, 5), (5, 0), (10, 5), (5, 10)],
        '1': [(0, 0), (3, 0), (3, 10), (0, 10)],
        '2': [(0, 0), (10, 0), (10, 3), (3, 3), (3, 5), (10, 5), (10, 10), (0, 10), (0, 8), (8, 8), (8, 6), (0, 6)],
        '3': [(0, 0), (10, 0), (10, 10), (0, 10), (0, 8), (5, 8), (5, 6), (3, 6), (3, 4), (6, 4), (6, 2), (0, 2)],
        '4': [(8, 0), (10, 0), (10, 10), (7, 10), (7, 7), (2, 7), (2, 10), (0, 10), (0, 4), (5, 4)],
        '5': [(0, 0), (10, 0), (10, 5), (5, 5), (5, 8), (10, 8), (10, 10), (0, 10), (0, 4), (8, 4), (8, 2), (0, 2)],
        '6': [(0, 0), (10, 0), (10, 5), (5, 5), (5, 8), (10, 8), (10, 10), (0, 10), (0, 4), (8, 4), (8, 2), (4, 2), (4, 4), (0, 4)],
        '7': [(8, 0), (10, 0), (10, 10), (0, 10), (0, 7), (7, 7)],
        '8': [(0, 0), (10, 0), (10, 5), (5, 5), (5, 8), (8, 8), (8, 5), (10, 5), (10, 8), (10, 10), (0, 10), (0, 4), (8, 4), (8, 2), (4, 2), (4, 4), (0, 4)],
        '9': [(0, 0), (10, 0), (10, 5), (5, 5), (5, 8), (8, 8), (8, 5), (10, 5), (10, 8), (10, 10), (0, 10), (0, 4), (8, 4), (8, 2), (0, 2)],
        'a': [(0, 0), (5, 3), (10, 0), (5, 10)],
        'b': [(0, 0), (5, 4), (2, 7), (0, 13)],
        'c': [(0, 5), (7, 0), (4, 5), (7, 10)],
        'd': [(0, 0), (10, 0), (5, 10)],
        'e': [(0, 5), (7, 0), (4, 5), (9, 5), (4.5, 10)],
        'f': [(0, 0), (10, 0), (5, 10)],
        'g': [(0, 5), (7, 0), (8, 5), (3.5, 5), (6, 10)],
        'h': [(0, 10), (0, 0), (3, 4.5), (6, 0), (6, 10), (3, 5.5)],
        'i': [(0, 5), (2, 0), (4, 5), (2, 10)],
        'j': [(0, 0), (10, 0), (5, 10)],
        'k': [(0, 0), (10, 0), (5, 10)],
        'l': [(0, 10), (2, 0), (8, 2), (4, 3)],
        'm': [(0, 0), (6, 2), (12, 0), (12, 10), (6, 3), (0, 10)],
        'n': [(0, 10), (0, 0), (2, 3.5), (6, 0), (6, 10), (4, 5)],
        'o': [(0, 5), (5, 0), (10, 5), (5, 10)],
        'p': [(0, 10), (0, 0), (2, 5), (6, 7.5)],
        'q': [(0, 0), (10, 0), (5, 10)],
        'r': [(0, 10), (0, 0), (2, 2), (7, 0), (2, 5), (6, 7.5)],
        's': [(0, 6), (3, 3), (0, 0), (6, 4), (3, 7), (6, 10)],
        't': [(0, 8), (4, 6.5), (5, 0), (6, 7), (10, 10)],
        'u': [(0, 0), (10, 0), (5, 10)],
        'v': [(0, 10), (5, 0), (10, 10), (5, 6)],
        'w': [(0, 0), (10, 0), (5, 10)],
        'x': [(0, 10), (3, 5), (0, 0), (5, 3), (10, 0), (7, 5), (10, 10), (5, 7)],
        'y': [(0, 10), (4, 5), (3, 0), (10, 10), (5, 7)],
        'z': [(0, 0), (10, 0), (5, 10)],
        '+': [(5, 10), (3.5, 6.5), (0, 5), (3.5, 3.5), (5, 0), (6.5, 3.5), (10, 5), (6.5, 6.5)],
    }

    def __init__(self, char, scale=1, **kwds):
        poly = self.LETTERS[char]
        super(Letter, self).__init__(poly, **kwds)
        self.scale(scale)
        self.move((-self.xmin, -self.ymin))
        self.char = char

KERNING = {
    'at':-3.7 , 'ti':-2.7, 'ga':-1.7, 'ha':-1, 'ca':-1, 'ro':-2.2,
    'le':-4.2, 'ev':-1.7, 've':-1.2, 'po':-1.2, 'ly':-3, 'yp': 0.5,
    'by':-2, 'ps':-2}

def add_word(word, world, scale=1, color='black', pos=(0, 0), **kwds):
    '''Adiciona a palavra ao mundo como uma sequência de letras. 
    
    Retorna a lista de objetos tipo Letter.'''

    if ' ' in word:
        letters = []
        x, y = pos
        for w in word.split(' '):
            letters.extend(add_word(w, world, scale=scale, color=color, pos=(x, y), **kwds))
            x = letters[-1].xmax + 10 * scale
        return letters

    def letter_adjust():
        if not letters:
            return
        last = letters[-1]
        letter.move((last.xmax, 0))
        letter.move((KERNING.get(last.char + letter.char, 0) * scale + 2 * scale, 0))

    letters = []
    for char in word:
        letter = Letter(char, scale=scale, color=color, **kwds)
        letter_adjust()
        letters.append(letter)

    for letter in letters:
        letter.move(pos)
        world.add(letter)

    return letters

if __name__ == '__main__':
    from FGAme import *

    world = World(gravity=0)
    add_word('polypong', world, scale=7, pos=(-300, 100))
    add_word('by chips', world, scale=4, pos=(-100, -50))
    world.add(Poly([(-400, -200), (-400, -300), (400, -300), (400, 0)], mass='inf'))
    world.run()
