"""
Quick matches without the server's printing.
usage: python bench_tournament.py [games] [seconds_per_move]
Plays the tournament agent against random, greedy and positional baselines,
alternating colours, and reports wins / time per move / depth reached.
"""
import random
import sys
import time

from advsearch.othello.board import Board
from advsearch.othello.gamestate import GameState
from advsearch.your_agent import tournament_agent as ta


def random_player(state, rng):
    return rng.choice(sorted(state.legal_moves()))


def greedy_player(state, rng):
    P, O = ta.to_bitboards(state)
    moves = sorted(state.legal_moves())
    return max(moves, key=lambda m: (ta.popcount(ta.flips(P, O, m[1] * 8 + m[0])), rng.random()))


def positional_player(state, rng):
    # 1-ply on the kit's mask, with opponent mobility as a tiebreak
    P, O = ta.to_bitboards(state)

    def score(m):
        sq = m[1] * 8 + m[0]
        f = ta.flips(P, O, sq)
        nP, nO = P | f | (1 << sq), O ^ f
        pos = sum(ta.SQ_WEIGHT[i] for i in range(64) if nP >> i & 1) - \
            sum(ta.SQ_WEIGHT[i] for i in range(64) if nO >> i & 1)
        return pos - 3 * ta.popcount(ta.gen_moves(nO, nP)) + rng.random()
    return max(sorted(state.legal_moves()), key=score)


def play(black, white, rng):
    state = GameState(Board(), 'B')
    players = {'B': black, 'W': white}
    while not state.is_terminal():
        state = state.next_state(players[state.player](state, rng))
    b, w = state.board.num_pieces('B'), state.board.num_pieces('W')
    return 'B' if b > w else 'W' if w > b else None


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    tl = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    stats = {'t': [], 'd': [], 'n': 0}

    def agent(state, rng):
        t = time.perf_counter()
        P, O = ta.to_bitboards(state)
        sq, depth, nodes = ta.best_move(P, O, tl)
        stats['t'].append(time.perf_counter() - t)
        stats['d'].append(depth)
        stats['n'] += nodes
        return sq % 8, sq // 8

    rng = random.Random(42)
    for name, opp in (('random', random_player), ('greedy', greedy_player),
                      ('positional', positional_player)):
        wins = draws = 0
        for g in range(games):
            if g % 2 == 0:
                w = play(agent, opp, rng); mine = 'B'
            else:
                w = play(opp, agent, rng); mine = 'W'
            wins += w == mine
            draws += w is None
        print(f'vs {name:10s}: {wins}/{games} wins, {draws} draws')
    ts = stats['t']
    print(f'moves={len(ts)} avg={sum(ts)/len(ts):.3f}s max={max(ts):.3f}s '
          f'avg depth={sum(stats["d"])/len(ts):.1f} nodes/s={stats["n"]/sum(ts):.0f}')


if __name__ == '__main__':
    main()
