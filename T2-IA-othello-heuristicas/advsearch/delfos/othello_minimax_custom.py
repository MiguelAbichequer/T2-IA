import random
from typing import Tuple
from ..othello.gamestate import GameState
from ..othello.board import Board
from .minimax import minimax_move

# Voce pode criar funcoes auxiliares neste arquivo
# e tambem modulos auxiliares neste pacote.
#
# Nao esqueca de renomear 'your_agent' com o nome
# do seu agente.


# profundidade calibrada para responder em < 5s
MAX_DEPTH = 4


def make_move(state) -> Tuple[int, int]:
    """
    Returns a move for the given game state
    :param state: state to make the move
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """

    return minimax_move(state, MAX_DEPTH, evaluate_custom)


def evaluate_custom(state, player:str) -> float:
    """
    Evaluates an othello state from the point of view of the given player. 
    If the state is terminal, returns its utility. 
    If non-terminal, returns an estimate of its value based on your custom heuristic
    :param state: state to evaluate (instance of GameState)
    :param player: player to evaluate the state for (B or W)
    """
    board = state.board
    opp = Board.opponent(player)
    my_pieces, opp_pieces = board.num_pieces(player), board.num_pieces(opp)

    if state.is_terminal():
        # vitoria/derrota domina qualquer avaliacao heuristica
        return WIN_SCORE * (my_pieces - opp_pieces)

    tiles = board.tiles
    corners = edges = x_squares = frontier = 0
    for (cy, cx), adjacent in CORNERS.items():
        corner = tiles[cy][cx]
        corners += (corner == player) - (corner == opp)
        if corner == Board.EMPTY:
            # casas vizinhas de quina vazia entregam a quina ao oponente
            for ay, ax in adjacent:
                x_squares += (tiles[ay][ax] == opp) - (tiles[ay][ax] == player)

    for y in range(8):
        for x in range(8):
            tile = tiles[y][x]
            if tile == Board.EMPTY:
                continue
            sign = 1 if tile == player else -1
            if x in (0, 7) or y in (0, 7):
                edges += sign
            # pecas de fronteira (vizinhas de vazio) costumam ser viradas
            for dx, dy in Board.DIRECTIONS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8 and tiles[ny][nx] == Board.EMPTY:
                    frontier -= sign
                    break

    my_moves, opp_moves = len(board.legal_moves(player)), len(board.legal_moves(opp))
    mobility = 100 * (my_moves - opp_moves) / (my_moves + opp_moves + 1)

    empty = board.num_pieces(Board.EMPTY)
    # no fim do jogo a contagem de pecas passa a importar
    parity = (my_pieces - opp_pieces) if empty < 16 else 0

    return (800 * corners + 300 * x_squares + 10 * mobility
            + 10 * edges + 15 * frontier + 10 * parity)


WIN_SCORE = 10000

# quina (y, x) -> casas adjacentes (C e X)
CORNERS = {
    (0, 0): [(0, 1), (1, 0), (1, 1)],
    (0, 7): [(0, 6), (1, 7), (1, 6)],
    (7, 0): [(7, 1), (6, 0), (6, 1)],
    (7, 7): [(7, 6), (6, 7), (6, 6)],
}
