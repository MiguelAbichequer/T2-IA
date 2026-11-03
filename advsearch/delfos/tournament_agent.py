import time
from typing import Tuple
from ..othello.gamestate import GameState
from ..othello.board import Board
from .othello_minimax_custom import evaluate_custom
from .othello_minimax_mask import EVAL_TEMPLATE

# tempo de busca por jogada (limite do torneio e' 5s; folga para copia de estado e servidor)
TIME_BUDGET = 4.0

# tipos de entrada na tabela de transposicao
EXACT, LOWER, UPPER = 0, 1, 2


class _Timeout(Exception):
    pass


def make_move(state) -> Tuple[int, int]:
    """
    Returns a move for the given game state.
    Consider that this will be called in the Othello tournament situation,
    so you should call the best implementation you got.

    Alfa-beta com aprofundamento iterativo parado por tempo, heuristica customizada,
    tabela de transposicao e ordenacao de jogadas.

    :param state: state to make the move
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """
    deadline = time.time() + TIME_BUDGET
    player = state.player
    moves = _ordered(state.legal_moves(), None)
    best_move = moves[0]
    if len(moves) == 1:
        return best_move

    # tabela de transposicao vale so' para esta jogada (jogador da raiz fixo)
    table = {}
    empty = state.board.num_pieces(Board.EMPTY)
    depth = 1
    while depth <= empty:
        try:
            best_move = _root(state, moves, depth, player, deadline, table)
        except _Timeout:
            break
        # a melhor jogada encontrada vai primeiro na proxima iteracao (mais podas)
        moves.remove(best_move)
        moves.insert(0, best_move)
        depth += 1
    return best_move


def _ordered(moves, first) -> list:
    """Ordena jogadas: 'first' (vinda da tabela) e depois pelo valor posicional."""
    ordered = sorted(moves, key=lambda m: EVAL_TEMPLATE[m[1]][m[0]], reverse=True)
    if first in moves:
        ordered.remove(first)
        ordered.insert(0, first)
    return ordered


def _next_state(state, move) -> GameState:
    """
    Equivalente a state.next_state, mas copia o tabuleiro direto (sem passar por string)
    e reaproveita o cache de jogadas legais. E' o gargalo da busca.
    """
    board, player = state.board, state.player
    new = object.__new__(Board)
    new.tiles = [row[:] for row in board.tiles]
    new.piece_count = dict(board.piece_count)
    new.flipped = set()
    # process_move consulta as jogadas legais de 'player' no tabuleiro antes da jogada
    new._legal_moves = {player: board.legal_moves(player), Board.opponent(player): None}
    new.process_move(move, player)

    opp = Board.opponent(player)
    if new.legal_moves(opp):
        next_player = opp
    elif new.legal_moves(player):
        next_player = player
    else:
        next_player = None
    return GameState(new, next_player)


def _key(state) -> str:
    return ''.join(map(''.join, state.board.tiles)) + str(state.player)


def _root(state, moves, depth, player, deadline, table):
    best_move, best_value = None, float('-inf')
    alpha, beta = float('-inf'), float('inf')
    for move in moves:
        value = _alphabeta(_next_state(state, move), depth - 1, alpha, beta, player, deadline, table)
        if best_move is None or value > best_value:
            best_move, best_value = move, value
        alpha = max(alpha, best_value)
    return best_move


def _alphabeta(state, depth, alpha, beta, player, deadline, table) -> float:
    if time.time() > deadline:
        raise _Timeout()
    if depth == 0 or state.player is None:   # player None == estado terminal
        return evaluate_custom(state, player)

    key = _key(state)
    entry = table.get(key)
    tt_move = None
    if entry is not None:
        e_depth, e_value, e_flag, tt_move = entry
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_value
            if e_flag == LOWER:
                alpha = max(alpha, e_value)
            else:
                beta = min(beta, e_value)
            if alpha >= beta:
                return e_value

    alpha0, beta0 = alpha, beta
    maximizing = state.player == player
    value = float('-inf') if maximizing else float('inf')
    best_move = None
    for move in _ordered(state.legal_moves(), tt_move):
        child = _alphabeta(_next_state(state, move), depth - 1, alpha, beta, player, deadline, table)
        if maximizing:
            if child > value:
                value, best_move = child, move
            alpha = max(alpha, value)
        else:
            if child < value:
                value, best_move = child, move
            beta = min(beta, value)
        if alpha >= beta:
            break

    if value <= alpha0:
        flag = UPPER
    elif value >= beta0:
        flag = LOWER
    else:
        flag = EXACT
    table[key] = (depth, value, flag, best_move)
    return value
