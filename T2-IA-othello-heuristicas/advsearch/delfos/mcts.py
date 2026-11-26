import math
import random
import time
from typing import Tuple

from .tournament_agent import _next_state as _othello_next_state

# tempo de busca por jogada (limite de 5s no Othello)
TIME_BUDGET = 4.0
# constante de exploracao do UCB1
EXPLORATION = math.sqrt(2)


class _Node:
    def __init__(self, state, parent=None, move=None, mover=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.mover = mover              # jogador que fez 'move' para chegar aqui
        self.children = []
        self.untried = [] if state.is_terminal() else list(state.legal_moves())
        self.wins = 0.0                 # do ponto de vista de 'mover'
        self.visits = 0

    def best_child(self):
        log_n = math.log(self.visits)
        return max(self.children, key=lambda c: c.wins / c.visits
                   + EXPLORATION * math.sqrt(log_n / c.visits))


def make_move(state) -> Tuple[int, int]:
    """
    Returns a move for the given game state.
    The game is not specified, but this is MCTS and should handle any game, since
    their implementation has the same interface.

    UCT: selecao por UCB1, expansao de um filho por iteracao, simulacao aleatoria
    ate o fim do jogo e retropropagacao (1 vitoria, 0.5 empate, 0 derrota).

    :param state: state to make the move
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """
    next_state = _othello_next_state if state.game_name == 'Othello' else _generic_next_state
    deadline = time.time() + TIME_BUDGET
    root = _Node(state)
    if len(root.untried) == 1:
        return root.untried[0]

    while time.time() < deadline:
        node = root
        # selecao
        while not node.untried and node.children:
            node = node.best_child()
        # expansao
        if node.untried:
            move = node.untried.pop(random.randrange(len(node.untried)))
            child = _Node(next_state(node.state, move), node, move, node.state.player)
            node.children.append(child)
            node = child
        # simulacao
        winner = _playout(node.state, next_state)
        # retropropagacao
        while node is not None:
            node.visits += 1
            if node.mover is not None:
                node.wins += 0.5 if winner is None else float(winner == node.mover)
            node = node.parent

        # arvore inteira explorada (jogos pequenos): nao ha' o que ganhar continuando
        if not root.untried and all(_solved(c) for c in root.children):
            break

    # mais visitado; empate (ex.: arvore pequena resolvida) desfeito pela taxa de vitoria
    return max(root.children, key=lambda c: (c.visits, c.wins / c.visits)).move


def _generic_next_state(state, move):
    return state.next_state(move)


def _playout(state, next_state):
    while not state.is_terminal():
        state = next_state(state, random.choice(list(state.legal_moves())))
    return state.winner()


def _solved(node) -> bool:
    if node.untried:
        return False
    return all(_solved(c) for c in node.children)
