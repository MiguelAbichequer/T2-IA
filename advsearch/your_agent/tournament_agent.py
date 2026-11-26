"""
Tournament Othello agent.

Bitboards (Python ints, bit = y*8 + x), negamax alpha-beta with PVS, iterative
deepening under a wall-clock budget, transposition table, mobility-based move
ordering and an exact endgame solve once depth reaches the number of empties.
"""
import time
from typing import Tuple

# Server default delay is 5s; a timeout counts as an illegal move.
# ponytail: fixed budget, raise if the tournament delay is known to be larger.
TIME_LIMIT = 4.0

FULL = (1 << 64) - 1
NOT_A = 0xfefefefefefefefe  # all squares except column x=0
NOT_H = 0x7f7f7f7f7f7f7f7f  # all squares except column x=7
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

try:
    popcount = int.bit_count  # python >= 3.10
except AttributeError:  # python 3.9 (the kit's reference interpreter)
    def popcount(x):
        return bin(x).count('1')

INF = 10 ** 9
WIN = 100000

def gen_moves(P, O):
    """Bitboard of legal moves for the player owning P (8 unrolled directional fills)."""
    e = ~(P | O) & FULL
    oa = O & NOT_A; oh = O & NOT_H
    # m: E/SE/NE (may wrap into column A), m2: W/NW/SW (column H), m3: N/S
    t = oa & (P << 1); t |= oa & (t << 1); t |= oa & (t << 1); t |= oa & (t << 1); t |= oa & (t << 1); t |= oa & (t << 1)
    m = t << 1
    t = oh & (P >> 1); t |= oh & (t >> 1); t |= oh & (t >> 1); t |= oh & (t >> 1); t |= oh & (t >> 1); t |= oh & (t >> 1)
    m2 = t >> 1
    t = O & (P << 8); t |= O & (t << 8); t |= O & (t << 8); t |= O & (t << 8); t |= O & (t << 8); t |= O & (t << 8)
    m3 = t << 8
    t = O & (P >> 8); t |= O & (t >> 8); t |= O & (t >> 8); t |= O & (t >> 8); t |= O & (t >> 8); t |= O & (t >> 8)
    m3 |= t >> 8
    t = oa & (P << 9); t |= oa & (t << 9); t |= oa & (t << 9); t |= oa & (t << 9); t |= oa & (t << 9); t |= oa & (t << 9)
    m |= t << 9
    t = oh & (P >> 9); t |= oh & (t >> 9); t |= oh & (t >> 9); t |= oh & (t >> 9); t |= oh & (t >> 9); t |= oh & (t >> 9)
    m2 |= t >> 9
    t = oh & (P << 7); t |= oh & (t << 7); t |= oh & (t << 7); t |= oh & (t << 7); t |= oh & (t << 7); t |= oh & (t << 7)
    m2 |= t << 7
    t = oa & (P >> 7); t |= oa & (t >> 7); t |= oa & (t >> 7); t |= oa & (t >> 7); t |= oa & (t >> 7); t |= oa & (t >> 7)
    m |= t >> 7
    return ((m & NOT_A) | (m2 & NOT_H) | m3) & e


def _build_rays():
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    rays = []
    for sq in range(64):
        x0, y0 = sq % 8, sq // 8
        lst = []
        for dx, dy in dirs:
            ray = []
            x, y = x0 + dx, y0 + dy
            while 0 <= x < 8 and 0 <= y < 8:
                ray.append(1 << (y * 8 + x))
                x += dx
                y += dy
            if len(ray) >= 2:
                lst.append(tuple(ray))
        rays.append(tuple(lst))
    return tuple(rays)


RAYS = _build_rays()


def flips(P, O, sq):
    """Discs flipped when the owner of P plays at sq."""
    f = 0
    for ray in RAYS[sq]:
        t = 0
        for b in ray:
            if O & b:
                t |= b
            elif P & b:
                f |= t
                break
            else:
                break
    return f


# ---------------------------------------------------------------- evaluation

def _bit(x, y):
    return 1 << (y * 8 + x)


# (corner, x-square, c-squares, edge walks from the corner)
CORNER_INFO = []
for cx, cy in ((0, 0), (7, 0), (0, 7), (7, 7)):
    dx = 1 if cx == 0 else -1
    dy = 1 if cy == 0 else -1
    edge1 = tuple(_bit(cx + dx * i, cy) for i in range(1, 8))
    edge2 = tuple(_bit(cx, cy + dy * i) for i in range(1, 8))
    CORNER_INFO.append((_bit(cx, cy), _bit(cx + dx, cy + dy),
                        _bit(cx + dx, cy) | _bit(cx, cy + dy), edge1, edge2))
CORNER_INFO = tuple(CORNER_INFO)

# static square weights, only used for cheap move ordering near leaves
SQ_WEIGHT = [
    100, -30, 6, 2, 2, 6, -30, 100,
    -30, -50, 1, 1, 1, 1, -50, -30,
    6, 1, 1, 1, 1, 1, 1, 6,
    2, 1, 1, 3, 3, 1, 1, 2,
    2, 1, 1, 3, 3, 1, 1, 2,
    6, 1, 1, 1, 1, 1, 1, 6,
    -30, -50, 1, 1, 1, 1, -50, -30,
    100, -30, 6, 2, 2, 6, -30, 100,
]

W_CORNER = 40
W_X = 18
W_C = 7
W_STABLE = 8
W_MOB = 7
W_FRONT = 3


def final_score(P, O):
    d = popcount(P) - popcount(O)
    if d > 0:
        return WIN + d
    if d < 0:
        return -WIN + d
    return 0


def evaluate(P, O):
    """Heuristic value for the side to move (owner of P)."""
    mP = popcount(gen_moves(P, O))
    mO = popcount(gen_moves(O, P))
    if not mP and not mO:
        return final_score(P, O)

    occ = P | O
    empty = ~occ & FULL
    empties = popcount(empty)

    s = W_MOB * (mP - mO)
    if mP == 0:
        s -= 15  # forced pass is bad
    elif mO == 0:
        s += 15

    for corner, xsq, csq, e1, e2 in CORNER_INFO:
        if P & corner:
            s += W_CORNER
            owner, sign = P, W_STABLE
        elif O & corner:
            s -= W_CORNER
            owner, sign = O, -W_STABLE
        else:
            # X/C squares only hurt while their corner is empty
            if P & xsq:
                s -= W_X
            elif O & xsq:
                s += W_X
            s -= W_C * (popcount(P & csq) - popcount(O & csq))
            continue
        # edge discs contiguous from an owned corner are stable
        for edge in (e1, e2):
            for b in edge:
                if owner & b:
                    s += sign
                else:
                    break

    # frontier: discs next to empty squares give the opponent moves
    e = empty
    nb = (((e << 1) & NOT_A) | ((e >> 1) & NOT_H) | (e << 8) | (e >> 8) |
          ((e << 9) & NOT_A) | ((e << 7) & NOT_H) | ((e >> 7) & NOT_A) | ((e >> 9) & NOT_H))
    s -= W_FRONT * (popcount(P & nb) - popcount(O & nb))

    if empties <= 20:
        # discs start to matter; parity favours the side making the last move
        s += (20 - empties) * (popcount(P) - popcount(O)) // 4
        s += 4 if empties & 1 else -4
    return s


# ---------------------------------------------------------------- search

EXACT, LOWER, UPPER = 0, 1, 2
TT = {}
TT_MAX = 1500000


class Timeout(Exception):
    pass


class Search:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0

    def tick(self):
        self.nodes += 1
        if not (self.nodes & 255) and time.perf_counter() > self.deadline:
            raise Timeout

    def solve(self, P, O, alpha, beta):
        """Exact endgame search (few empties): no TT, no heuristic."""
        self.tick()
        mv = gen_moves(P, O)
        if not mv:
            if not gen_moves(O, P):
                return final_score(P, O)
            return -self.solve(O, P, -beta, -alpha)
        best = -INF
        while mv:
            b = mv & -mv
            mv ^= b
            f = flips(P, O, b.bit_length() - 1)
            v = -self.solve(O ^ f, P | f | b, -beta, -alpha)
            if v > best:
                best = v
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        break
        return best

    def children(self, P, O, mv, depth, tt_move):
        kids = []
        while mv:
            b = mv & -mv
            mv ^= b
            sq = b.bit_length() - 1
            f = flips(P, O, sq)
            nP = O ^ f
            nO = P | f | b
            if sq == tt_move:
                key = -INF
            elif depth >= 3:
                # fastest-first: minimise opponent mobility, prefer corners
                key = popcount(gen_moves(nP, nO)) * 16 - SQ_WEIGHT[sq]
            else:
                key = -SQ_WEIGHT[sq]
            kids.append((key, sq, nP, nO))
        kids.sort()
        return kids

    def negamax(self, P, O, depth, alpha, beta):
        empties = 64 - popcount(P | O)
        if empties <= 7 and depth >= empties:
            return self.solve(P, O, alpha, beta)
        self.tick()

        key = (P, O)
        entry = TT.get(key)
        tt_move = -1
        if entry is not None:
            d, flag, val, tt_move = entry
            if d >= depth:
                if flag == EXACT:
                    return val
                if flag == LOWER:
                    if val >= beta:
                        return val
                elif val <= alpha:
                    return val

        if depth <= 0:
            return evaluate(P, O)

        mv = gen_moves(P, O)
        if not mv:
            if not gen_moves(O, P):
                return final_score(P, O)
            # pass: depth is not consumed, so depth >= empties stays exact
            return -self.negamax(O, P, depth, -beta, -alpha)

        alpha0 = alpha
        best = -INF
        best_sq = -1
        first = True
        for _, sq, nP, nO in self.children(P, O, mv, depth, tt_move):
            if first:
                v = -self.negamax(nP, nO, depth - 1, -beta, -alpha)
                first = False
            else:
                v = -self.negamax(nP, nO, depth - 1, -alpha - 1, -alpha)
                if alpha < v < beta:
                    v = -self.negamax(nP, nO, depth - 1, -beta, -v)
            if v > best:
                best, best_sq = v, sq
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        break

        if best <= alpha0:
            flag = UPPER
        elif best >= beta:
            flag = LOWER
        else:
            flag = EXACT
        TT[key] = (depth, flag, best, best_sq)
        return best

    def root(self, P, O, depth, order):
        """Searches root moves in `order`; returns (best_sq, score, order)."""
        alpha = -INF
        scored = []
        best_sq = order[0][1]
        try:
            for i, (sq, nP, nO) in enumerate(order):
                if i == 0:
                    v = -self.negamax(nP, nO, depth - 1, -INF, -alpha)
                else:
                    v = -self.negamax(nP, nO, depth - 1, -alpha - 1, -alpha)
                    if v > alpha:
                        v = -self.negamax(nP, nO, depth - 1, -INF, -alpha)
                scored.append((v, i))
                if v > alpha:
                    alpha, best_sq = v, sq
        except Timeout:
            # moves fully searched at this depth are still trustworthy:
            # the previous best is searched first, so a replacement is better
            if scored:
                raise PartialResult(best_sq)
            raise
        scored.sort(key=lambda t: (-t[0], t[1]))
        return best_sq, alpha, [order[i] for _, i in scored]


class PartialResult(Exception):
    def __init__(self, sq):
        self.sq = sq


def best_move(P, O, time_limit=TIME_LIMIT):
    """Returns (square, depth reached, nodes) for the owner of P."""
    start = time.perf_counter()
    mv = gen_moves(P, O)
    order = []
    while mv:
        b = mv & -mv
        mv ^= b
        sq = b.bit_length() - 1
        f = flips(P, O, sq)
        order.append((sq, O ^ f, P | f | b))
    if len(order) == 1:
        return order[0][0], 0, 0
    order.sort(key=lambda t: -SQ_WEIGHT[t[0]])

    if len(TT) > TT_MAX:
        TT.clear()

    search = Search(start + time_limit)
    empties = 64 - popcount(P | O)
    best_sq, done = order[0][0], 0
    depth = 1
    while depth <= empties:
        try:
            best_sq, score, order = search.root(P, O, depth, order)
        except PartialResult as pr:
            best_sq = pr.sq
            break
        except Timeout:
            break
        done = depth
        elapsed = time.perf_counter() - start
        # exact result, or a proven win/loss, or next iteration will not finish
        if abs(score) >= WIN or elapsed > time_limit * 0.45:
            break
        depth += 1
    return best_sq, done, search.nodes


def to_bitboards(state):
    tiles = state.board.tiles
    me = state.player
    opp = 'W' if me == 'B' else 'B'
    P = O = 0
    for y in range(8):
        row = tiles[y]
        for x in range(8):
            c = row[x]
            if c == me:
                P |= 1 << (y * 8 + x)
            elif c == opp:
                O |= 1 << (y * 8 + x)
    return P, O


def make_move(state) -> Tuple[int, int]:
    """
    Returns a move for the given game state.
    :param state: state to make the move
    :return: (int, int) tuple with x, y coordinates of the move (remember: 0 is the first row/column)
    """
    try:
        P, O = to_bitboards(state)
        sq, _, _ = best_move(P, O)
        return sq % 8, sq // 8
    except Exception:
        # never forfeit a turn on a bug: fall back to any legal move
        moves = sorted(state.legal_moves())
        return moves[0] if moves else (-1, -1)
