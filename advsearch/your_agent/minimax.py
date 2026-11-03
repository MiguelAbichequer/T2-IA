import random
from typing import Tuple, Callable



def minimax_move(state, max_depth:int, eval_func:Callable) -> Tuple[int, int]:
    """
    Returns a move computed by the minimax algorithm with alpha-beta pruning for the given game state.
    :param state: state to make the move (instance of GameState)
    :param max_depth: maximum depth of search (-1 = unlimited)
    :param eval_func: the function to evaluate a terminal or leaf state (when search is interrupted at max_depth)
                    This function should take a GameState object and a string identifying the player,
                    and should return a float value representing the utility of the state for the player.
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """
    player = state.player
    best_move, best_value = None, float('-inf')
    alpha, beta = float('-inf'), float('inf')
    for move in state.legal_moves():
        value = _alphabeta(state.next_state(move), max_depth - 1, alpha, beta, player, eval_func)
        if value > best_value or best_move is None:
            best_move, best_value = move, value
        alpha = max(alpha, best_value)
    return best_move


def _alphabeta(state, depth: int, alpha: float, beta: float, player: str, eval_func: Callable) -> float:
    """
    Value of state for 'player'. depth < 0 means unlimited.
    MAX/MIN is decided by who moves (state.player), so passes in Othello are handled.
    """
    if depth == 0 or state.is_terminal():
        return eval_func(state, player)

    if state.player == player:
        value = float('-inf')
        for move in state.legal_moves():
            value = max(value, _alphabeta(state.next_state(move), depth - 1, alpha, beta, player, eval_func))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = float('inf')
        for move in state.legal_moves():
            value = min(value, _alphabeta(state.next_state(move), depth - 1, alpha, beta, player, eval_func))
            beta = min(beta, value)
            if alpha >= beta:
                break
    return value
