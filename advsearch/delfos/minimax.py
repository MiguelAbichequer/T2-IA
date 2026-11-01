from typing import Tuple, Callable


def minimax_move(state, max_depth: int, eval_func: Callable) -> Tuple[int, int]:
    """
    Returns a move computed by the minimax algorithm with alpha-beta pruning for the given game state.
    :param state: state to make the move (instance of GameState)
    :param max_depth: maximum depth of search (-1 = unlimited)
    :param eval_func: the function to evaluate a terminal or leaf state (when search is interrupted at max_depth)
                    This function should take a GameState object and a string identifying the player,
                    and should return a float value representing the utility of the state for the player.
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """
    root_player = state.player

    def search(s, depth: int, alpha: float, beta: float) -> float:
        # folha: estado terminal ou limite de profundidade atingido
        if s.is_terminal() or (max_depth != -1 and depth >= max_depth):
            return eval_func(s, root_player)
        if s.player == root_player:
            value = float('-inf')
            for move in s.legal_moves():
                value = max(value, search(s.next_state(move), depth + 1, alpha, beta))
                if value >= beta:# poda beta
                    return value
                alpha = max(alpha, value)
            return value
        else:
            value = float('inf')
            for move in s.legal_moves():
                value = min(value, search(s.next_state(move), depth + 1, alpha, beta))
                if value <= alpha:# poda alfa
                    return value
                beta = min(beta, value)
            return value

    best_move = None
    best_value = float('-inf')
    alpha, beta = float('-inf'), float('inf')

    for move in state.legal_moves():
        if best_move is None:
            best_move = move             # garante que sempre retornamos uma jogada valida
        value = search(state.next_state(move), 1, alpha, beta)
        if value > best_value:
            best_value, best_move = value, move
        alpha = max(alpha, best_value)

    return best_move