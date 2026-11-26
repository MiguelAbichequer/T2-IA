"""
Agente de torneio (versao 2).

Busca: negamax com alfa-beta, aprofundamento iterativo limitado pelo tempo,
tabela de transposicao e ordenacao de jogadas (melhor jogada anterior, depois
tabela posicional). Quando as casas vazias sao poucas, a profundidade de
aprofundamento chega ao fim do jogo e a busca passa a ser exata.

Mudancas em relacao a versao 1 (tournament_agent_v1.py):
  * motor de bitboards (advsearch/delfos/bitboard.py) em vez de listas e
    varredura de casas; o estado de busca e' so' dois inteiros;
  * avaliacao por fases com estabilidade, mobilidade potencial e fronteira
    (advsearch/delfos/othello_eval.py);
  * passes nao consomem profundidade, entao a busca e' exata no final;
  * ordenacao na raiz usa os valores da iteracao anterior.
"""
import time
from typing import Tuple

from . import bitboard as bb
from .othello_eval import evaluate, terminal_value, SQ_VALUE

# tempo de busca por jogada (limite do torneio e' 5s; folga para o servidor)
TIME_BUDGET = 4.0
# limite de entradas na tabela de transposicao (controle de memoria)
TT_LIMIT = 1_000_000

INF = 10 ** 9
EXACT, LOWER, UPPER = 0, 1, 2
_NEG_SQ = [-v for v in SQ_VALUE]

STATS = {'nodes': 0, 'last_depth': 0}


class _Timeout(Exception):
    pass


def make_move(state) -> Tuple[int, int]:
    """
    Retorna a jogada (x, y) para o estado dado.
    :param state: GameState do projeto
    :return: (int, int) com coluna (x) e linha (y), a partir de 0
    """
    p, o = bb.from_gamestate(state)
    moves = _ordered(bb.legal_moves(p, o), None)
    best = moves[0]
    if len(moves) == 1:
        return bb.bit_to_xy(best)

    deadline = time.perf_counter() + TIME_BUDGET
    tt = {}
    empties = 64 - bb.popcount(p | o)
    depth = 1
    while depth <= empties:
        try:
            best, scores = _root(p, o, moves, depth, deadline, tt)
        except _Timeout:
            break
        STATS['last_depth'] = depth
        moves = sorted(moves, key=lambda m: -scores[m])   # melhores primeiro na proxima iteracao
        depth += 1
    return bb.bit_to_xy(best)


def _ordered(moves, first):
    """Lista de indices de bit das jogadas, melhor posicionalmente primeiro; 'first' na frente."""
    lst = []
    m = moves
    while m:
        low = m & -m
        lst.append(low.bit_length() - 1)
        m ^= low
    lst.sort(key=_NEG_SQ.__getitem__)
    if first is not None and first in lst:
        lst.remove(first)
        lst.insert(0, first)
    return lst


def _root(p, o, moves, depth, deadline, tt):
    best_move, best_value = None, -INF
    scores = {}
    alpha, beta = -INF, INF
    for m in moves:
        np_, no_ = bb.apply_move(p, o, 1 << m)
        v = -_negamax(no_, np_, depth - 1, -beta, -alpha, deadline, tt)
        scores[m] = v
        if best_move is None or v > best_value:
            best_move, best_value = m, v
        alpha = max(alpha, best_value)
    return best_move, scores


def _negamax(p, o, depth, alpha, beta, deadline, tt) -> float:
    """Valor do estado do ponto de vista de p (quem esta' jogando)."""
    STATS['nodes'] += 1
    if time.perf_counter() > deadline:
        raise _Timeout()

    mp = bb.legal_moves(p, o)
    if not mp:
        mo = bb.legal_moves(o, p)
        if not mo:
            return terminal_value(p, o)
        # passe: nao consome profundidade (nao ha' ramificacao)
        return -_negamax(o, p, depth, -beta, -alpha, deadline, tt)

    if depth == 0:
        return evaluate(p, o, mp)

    key = (p, o)
    tt_move = None
    entry = tt.get(key)
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
    best_value, best_move = -INF, None
    for m in _ordered(mp, tt_move):
        np_, no_ = bb.apply_move(p, o, 1 << m)
        v = -_negamax(no_, np_, depth - 1, -beta, -alpha, deadline, tt)
        if v > best_value:
            best_value, best_move = v, m
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break

    if best_value <= alpha0:
        flag = UPPER
    elif best_value >= beta0:
        flag = LOWER
    else:
        flag = EXACT
    if len(tt) >= TT_LIMIT:
        tt.clear()
    tt[key] = (depth, best_value, flag, best_move)
    return best_value
