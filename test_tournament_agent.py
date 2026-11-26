import random
import time
import unittest

from advsearch.othello.board import Board
from advsearch.othello.gamestate import GameState
from advsearch.your_agent import tournament_agent as ta


def bits_to_moves(m):
    return {(sq % 8, sq // 8) for sq in range(64) if m >> sq & 1}


class TestTournamentAgent(unittest.TestCase):
    def test_movegen_and_flips_match_board(self):
        rng = random.Random(0)
        for _ in range(60):
            state = GameState(Board(), 'B')
            while not state.is_terminal():
                P, O = ta.to_bitboards(state)
                self.assertEqual(bits_to_moves(ta.gen_moves(P, O)), state.legal_moves())
                move = rng.choice(sorted(state.legal_moves()))
                nxt = state.next_state(move)
                sq = move[1] * 8 + move[0]
                f = ta.flips(P, O, sq)
                # after the move, the mover's discs are P|f|b
                mover = GameState(nxt.board, state.player)
                self.assertEqual(ta.to_bitboards(mover)[0], P | f | (1 << sq))
                state = nxt

    def test_pass_and_endgame(self):
        # W has no move; B must still be able to move and get an exact answer
        board = Board.from_string("""BBBBBBBB
BBBBBBBB
BBBBBBBB
BBBBBBBB
BBBBBBBB
BBBBBBWW
BBBBBBW.
BBBBBB..""")
        state = GameState(board, 'B')
        move = ta.make_move(state)
        self.assertIn(move, state.legal_moves())

    def test_returns_legal_move_in_time(self):
        rng = random.Random(1)
        state = GameState(Board(), 'B')
        for _ in range(20):
            if state.is_terminal():
                break
            t = time.perf_counter()
            P, O = ta.to_bitboards(state)
            sq, _, _ = ta.best_move(P, O, 0.3)
            self.assertLess(time.perf_counter() - t, 0.6)
            self.assertIn((sq % 8, sq // 8), state.legal_moves())
            state = state.next_state(rng.choice(sorted(state.legal_moves())))


if __name__ == '__main__':
    unittest.main()
