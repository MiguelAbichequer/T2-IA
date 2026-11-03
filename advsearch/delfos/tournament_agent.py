import time
from typing import Tuple
from ..othello.gamestate import GameState
from ..othello.board import Board
from .othello_minimax_custom import evaluate_custom
from .othello_minimax_mask import EVAL_TEMPLATE

# tempo de busca por jogada (limite do torneio e' 5s; folga para copia de estado e servidor)
TIME_BUDGET = 4.0


class _Timeout(Exception):
    pass


def make_move(state) -> Tuple[int, int]:
    """
    Returns a move for the given game state.
    Consider that this will be called in the Othello tournament situation,
    so you should call the best implementation you got.

    Alfa-beta com aprofundamento iterativo parado por tempo, heuristica customizada
    e ordenacao de jogadas (melhor jogada da iteracao anterior primeiro, depois mascara posicional).

    :param state: state to make the move
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """
    deadline = time.time() + TIME_BUDGET
    player = state.player
    moves = _ordered(state.legal_moves())
    best_move = moves[0]
    if len(moves) == 1:
        return best_move

    empty = state.board.num_pieces(Board.EMPTY)
    depth = 1
    while depth <= empty:
        try:
            best_move = _root(state, moves, depth, player, deadline)
        except _Timeout:
            break
        # a melhor jogada encontrada vai primeiro na proxima iteracao (mais podas)
        moves.remove(best_move)
        moves.insert(0, best_move)
        depth += 1
    return best_move


def _ordered(moves) -> list:
    """Ordena jogadas pelo valor posicional (quinas primeiro, casas X por ultimo)."""
    return sorted(moves, key=lambda m: EVAL_TEMPLATE[m[1]][m[0]], reverse=True)


def _root(state, moves, depth, player, deadline):
    best_move, best_value = None, float('-inf')
    alpha, beta = float('-inf'), float('inf')
    for move in moves:
        value = _alphabeta(state.next_state(move), depth - 1, alpha, beta, player, deadline)
        if best_move is None or value > best_value:
            best_move, best_value = move, value
        alpha = max(alpha, best_value)
    return best_move


def _alphabeta(state, depth, alpha, beta, player, deadline) -> float:
    if time.time() > deadline:
        raise _Timeout()
    if depth == 0 or state.is_terminal():
        return evaluate_custom(state, player)

    maximizing = state.player == player
    value = float('-inf') if maximizing else float('inf')
    for move in _ordered(state.legal_moves()):
        child = _alphabeta(state.next_state(move), depth - 1, alpha, beta, player, deadline)
        if maximizing:
            value = max(value, child)
            alpha = max(alpha, value)
        else:
            value = min(value, child)
            beta = min(beta, value)
        if alpha >= beta:
            break
    return value
