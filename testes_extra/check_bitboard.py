import sys, random
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from advsearch.delfos import bitboard as bb
import refengine as ref

def to_bits_grid(g, c):
    return bb.to_bits([''.join(r) for r in g], c)

def random_finish(g, p, rnd):
    """Continuacao aleatoria ate o fim (com passes). Retorna o tabuleiro final."""
    while p is not None:
        ms = ref.legal(g, p)
        m = rnd.choice(sorted(ms))
        g = ref.play(g, m[0], m[1], p)
        p = ref.next_player(g, p)
    return g

rnd = random.Random(3)
n_pos = 0; n_stable_checks = 0
for game in range(300):
    g = ref.initial(); p = 'B'
    while p is not None:
        P = to_bits_grid(g, p); O = to_bits_grid(g, 'W' if p=='B' else 'B')
        lm = bb.legal_moves(P, O)
        ref_set = ref.legal(g, p)
        got = {bb.bit_to_xy(i) for i in range(64) if lm >> i & 1}
        assert got == ref_set, (game, got ^ ref_set)
        for (x, y) in ref_set:
            m = 1 << (y*8+x)
            np_, no_ = bb.apply_move(P, O, m)
            g2 = ref.play(g, x, y, p)
            assert (np_, no_) == (to_bits_grid(g2, p), to_bits_grid(g2, 'W' if p=='B' else 'B'))
        S = bb.stable_discs(P, O)
        assert S & ~P == 0
        for c in (0, 7, 56, 63):
            if P >> c & 1: assert S >> c & 1
        # Solidez: discos estaveis nao podem mudar de cor em nenhuma continuacao
        if S and n_pos % 5 == 0:
            for _ in range(3):
                fin = random_finish(g, p, rnd)
                fin_P = to_bits_grid(fin, p)
                assert S & ~fin_P == 0, "disco 'estavel' foi virado!"
                n_stable_checks += 1
        n_pos += 1
        if not ref_set: break
        m = rnd.choice(sorted(ref_set))
        g = ref.play(g, m[0], m[1], p)
        p = ref.next_player(g, p)
print("posicoes verificadas:", n_pos, "| checagens de estabilidade (continuacoes):", n_stable_checks)
