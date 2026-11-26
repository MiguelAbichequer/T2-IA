"""
Harness de partidas entre dois agentes (mesmo codigo do projeto).
- Aberturas aleatorias (K lances) compartilhadas: cada abertura e' jogada duas vezes, trocando as cores.
- Cada jogada e' validada pelo motor de referencia independente.
- Registra vitorias, empates, diferenca de discos, tempo por jogada e erros.
uso: python3 match.py <projeto> <modA> <modB> <n_aberturas> <budget_s> <K> <saida.json> [budgetA budgetB]
"""
import sys, json, time, random, importlib
PROJ = sys.argv[1]
sys.path.insert(0, PROJ)
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from advsearch.othello.board import Board
from advsearch.othello.gamestate import GameState
import refengine as ref

def load(modname):
    return importlib.import_module(modname)

def opening(K, rnd):
    st = GameState(Board(), 'B')
    seq = []
    for _ in range(K):
        if st.player is None: break
        m = rnd.choice(sorted(st.legal_moves()))
        seq.append(m); st = st.next_state(m)
    return seq

def play(agents, budgets, seq, colour_a):
    """agents: {'B': mod, 'W': mod}. Retorna (discos_B, discos_W, erros, tempos por modulo)."""
    st = GameState(Board(), 'B')
    g = ref.initial(); p = 'B'
    times = {'B': [], 'W': []}; errors = {'B': 0, 'W': 0}
    for m in seq:                       # abertura (sem chamar agentes)
        st = st.next_state(m); g = ref.play(g, m[0], m[1], p); p = ref.next_player(g, p)
    while st.player is not None:
        c = st.player
        mod = agents[c]
        mod.TIME_BUDGET = budgets[c]
        t0 = time.time()
        mv = mod.make_move(st.copy() if hasattr(st, 'copy') else st)
        dt = time.time() - t0
        times[c].append(dt)
        mv = tuple(mv)
        if not st.is_legal_move(mv) or mv not in ref.legal(g, c):
            errors[c] += 1
            raise RuntimeError(f"jogada ilegal de {c}: {mv}")
        st = st.next_state(mv); g = ref.play(g, mv[0], mv[1], c)
        p = ref.next_player(g, c)
        assert (st.player == p) or (st.player is None and p is None)
    b, w = st.board.num_pieces('B'), st.board.num_pieces('W')
    return b, w, errors, times

if __name__ == '__main__':
    modA, modB = load(sys.argv[2]), load(sys.argv[3])
    n_open, budget, K = int(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])
    out = sys.argv[7]
    bA = float(sys.argv[8]) if len(sys.argv) > 8 else budget
    bB = float(sys.argv[9]) if len(sys.argv) > 9 else budget
    rnd = random.Random(2026)
    results = []
    wins = {'A': 0, 'B': 0, 'draw': 0}; diff_sum = 0; tA = []; tB = []
    t_start = time.time()
    for i in range(n_open):
        seq = opening(K, rnd)
        for colA in ('B', 'W'):
            colB = 'W' if colA == 'B' else 'B'
            agents = {colA: modA, colB: modB}
            budgets = {colA: bA, colB: bB}
            b, w, err, times = play(agents, budgets, seq, colA)
            dA = b - w if colA == 'B' else w - b          # diferenca de discos do ponto de vista de A
            diff_sum += dA
            res = 'A' if dA > 0 else ('B' if dA < 0 else 'draw')
            wins[res if res != 'draw' else 'draw'] += 1
            tA += times[colA]; tB += times[colB]
            results.append({'opening': i, 'colorA': colA, 'black': b, 'white': w, 'resultA': res,
                            'errA': err[colA], 'errB': err[colB]})
            print(f"abertura {i} A={colA}: {b}-{w} -> {res}  ({time.time()-t_start:.0f}s)", flush=True)
    n = len(results)
    summary = {'A': sys.argv[2], 'B': sys.argv[3], 'jogos': n, 'vitorias_A': wins['A'],
               'vitorias_B': wins['B'], 'empates': wins['draw'],
               'dif_discos_medio_A': diff_sum / n,
               'tempo_medio_A_s': sum(tA)/max(1,len(tA)), 'tempo_max_A_s': max(tA) if tA else 0,
               'tempo_medio_B_s': sum(tB)/max(1,len(tB)), 'tempo_max_B_s': max(tB) if tB else 0,
               'orcamento_A': bA, 'orcamento_B': bB, 'K': K}
    json.dump({'resumo': summary, 'jogos': results}, open(out, 'w'), indent=1)
    print(json.dumps(summary, indent=1))
