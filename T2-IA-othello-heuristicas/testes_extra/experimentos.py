"""
Experimentos de ablacao: cada variante muda um peso da avaliacao (novo motor)
e joga contra a versao antiga (tournament_agent_v1), com o mesmo orcamento e
as mesmas aberturas (ver match.py).

uso (na raiz do projeto):
    python testes_extra\\experimentos.py [n_aberturas] [segundos_por_jogada]
padrao: 12 aberturas, 0.5 s por jogada.  Saida: experimentos_resumo.json
"""
import os, sys, json, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DELFOS = os.path.join(ROOT, 'advsearch', 'delfos')

# nome -> alteracoes em othello_eval.W (abertura, final) ou DISC_SLOPE
VARIANTES = {
    'base':             {},                                  # controle: avaliacao atual
    'mob_forte':        {'mobility': (1000.0, 1000.0)},      # escala da avaliacao antiga
    'sem_posicao':      {'position': (0.0, 0.0)},            # sem tabela posicional
    'sem_estabilidade': {'stable': (0.0, 0.0)},              # sem discos estaveis
    'sem_potmob':       {'potmob': (0.0, 0.0)},              # sem mobilidade potencial
    'sem_perigo':       {'danger': (0.0, 0.0)},              # sem penalidade X/C
}

TEMPLATE = '''"""Variante {nome} (gerada por testes_extra/experimentos.py)."""
from . import othello_eval as _E
from . import tournament_agent as _T

TIME_BUDGET = {budget}
_E.W.update({pesos!r})


def make_move(state):
    _T.TIME_BUDGET = TIME_BUDGET
    return _T.make_move(state)
'''


def criar_variantes(budget):
    for nome, pesos in VARIANTES.items():
        path = os.path.join(DELFOS, 'variant_%s.py' % nome)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE.format(nome=nome, budget=budget, pesos=pesos))


def main():
    n_open = sys.argv[1] if len(sys.argv) > 1 else '12'
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    criar_variantes(budget)
    resumo = {}
    for nome in VARIANTES:
        out = os.path.join(ROOT, 'exp_%s.json' % nome)
        log = os.path.join(ROOT, 'exp_%s.log' % nome)
        print('>>> variante', nome, flush=True)
        with open(log, 'w', encoding='utf-8') as lf:
            subprocess.run([sys.executable, os.path.join('testes_extra', 'match.py'), ROOT,
                            'advsearch.delfos.variant_%s' % nome,
                            'advsearch.delfos.tournament_agent_v1',
                            str(n_open), str(budget), '6', out],
                           cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, check=True)
        r = json.load(open(out, encoding='utf-8'))['resumo']
        resumo[nome] = {'vitorias': r['vitorias_A'], 'derrotas': r['vitorias_B'],
                        'empates': r['empates'], 'dif_discos_medio': round(r['dif_discos_medio_A'], 2)}
        print('    ', resumo[nome], flush=True)
    json.dump(resumo, open(os.path.join(ROOT, 'experimentos_resumo.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print('\nResumo (variante contra tournament_agent_v1):')
    for nome, r in resumo.items():
        print('%-18s V=%3d  D=%3d  E=%3d  dif_discos=%+.2f' % (nome, r['vitorias'], r['derrotas'],
                                                              r['empates'], r['dif_discos_medio']))


if __name__ == '__main__':
    main()
