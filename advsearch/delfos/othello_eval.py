"""
Funcao de avaliacao posicional do agente de torneio (versao 2).

Ideias extraidas da bibliografia e como viraram termos:

  Lazard (estrategia)              -> termo
  ------------------------------------------------------------------------
  cantos e estabilidade            -> corners, stable (discos estaveis)
  C e X perigosos com canto vazio  -> danger (penaliza C/X do proprio lado)
  mobilidade                       -> mobility (jogadas legais, normalizada)
  mobilidade potencial             -> potmob (casas vazias adjacentes ao adversario)
  fronteira (minimizar)            -> frontier (discos adjacentes a casas vazias)
  controle do centro / posicional  -> position (tabela de Hasegawa, 'Basic Diagram')
  maximo de discos e' armadilha    -> disc (peso zero ate o final, depois cresce)

  Hasegawa (fases)                 -> pesos interpolados entre abertura e final.
                                      Abertura: posicional, mobilidade e fronteira.
                                      Final: estabilidade e contagem de discos.

Convencao: p e' o jogador a mover, o e' o adversario; valor > 0 favorece p.
Valores terminais (sem jogadas para ambos) usam WIN_VALUE, maior que qualquer
avaliacao heuristica, para que vitoria/derrota sempre dominem.
"""
from .bitboard import FULL, CORNERS, popcount, legal_moves, neighbours, stable_discs, shift

WIN_VALUE = 100000

# Tabela posicional (Hasegawa, 'Basic Diagram'): quadrante superior esquerdo,
# replicado por simetria. Corresponde a: canto=100, C=-20, X=-50, A=20, B=10,
# casas 'a'=3, 'b'=1..2, centro=0.
_QUAD = [
    [100, -20, 20, 10],
    [-20, -50, 3, 3],
    [20, 3, 2, 1],
    [10, 3, 1, 0],
]
SQ_VALUE = [0] * 64
for _i in range(64):
    _x, _y = _i % 8, _i // 8
    SQ_VALUE[_i] = _QUAD[min(_y, 7 - _y)][min(_x, 7 - _x)]

# tabelas por byte para somar a tabela posicional de um bitboard em 8 consultas
_BYTE_LUT = []
for _k in range(8):
    _row = []
    for _byte in range(256):
        _s = 0
        for _j in range(8):
            if _byte >> _j & 1:
                _s += SQ_VALUE[8 * _k + _j]
        _row.append(_s)
    _BYTE_LUT.append(_row)


def position_sum(bits):
    s = 0
    for k in range(8):
        s += _BYTE_LUT[k][(bits >> (8 * k)) & 255]
    return s


# casas X (diagonais dos cantos) e C (adjacentes ao longo da borda) de cada canto
_CORNER_X = [(0, 9), (7, 14), (56, 49), (63, 54)]     # (canto, casa X)
_CORNER_C = [(0, (1, 8)), (7, (6, 15)), (56, (48, 57)), (63, (55, 62))]
_X_BITS = [(1 << c, 1 << x) for c, x in _CORNER_X]
_C_BITS = [(1 << c, (1 << a) | (1 << b)) for c, (a, b) in _CORNER_C]


def _danger(p, o):
    """Pontuacao negativa para p quando ocupa X/C com o canto vazio (adversario pode pegar o canto)."""
    d = 0
    for (cbit, xbit), (_, cbits) in zip(_X_BITS, _C_BITS):
        if cbit & (p | o):
            continue
        d -= 2 * popcount(p & xbit) + popcount(p & cbits)
        d += 2 * popcount(o & xbit) + popcount(o & cbits)
    return d


def _lerp(a, b, t):
    return a + (b - a) * t


# pesos (abertura, final); o valor efetivo e' interpolado pela fase t em [0, 1]
W = {
    'corner': (800.0, 800.0),
    'stable': (40.0, 100.0),
    'mobility': (120.0, 25.0),
    'potmob': (60.0, 10.0),
    'frontier': (80.0, 10.0),
    'position': (1.0, 0.4),
    'danger': (120.0, 50.0),
}
DISC_SLOPE = 5.0          # peso por disco de diferenca, cresce quando faltam < 20 casas


def evaluate(p, o, mp=None, mo=None):
    """
    Avaliacao heuristica (nao terminal) do estado do ponto de vista de p.
    mp/mo podem ser passados (bitboards de jogadas legais) para evitar recalculo.
    """
    occupied = p | o
    empties = 64 - popcount(occupied)
    t = 1.0 - empties / 60.0
    empty = FULL & ~occupied

    if mp is None:
        mp = legal_moves(p, o)
    if mo is None:
        mo = legal_moves(o, p)
    nmp, nmo = popcount(mp), popcount(mo)

    corners = popcount(p & CORNERS) - popcount(o & CORNERS)
    stable = popcount(stable_discs(p, o)) - popcount(stable_discs(o, p))
    mobility = (nmp - nmo) / (nmp + nmo + 1.0)

    # mobilidade potencial: casas vazias que cada lado ainda pode alcancar
    nb_o = neighbours(o)
    nb_p = neighbours(p)
    pot_p = popcount(empty & nb_o)
    pot_o = popcount(empty & nb_p)
    potmob = (pot_p - pot_o) / (pot_p + pot_o + 1.0)

    # fronteira: discos adjacentes a casas vazias (queremos ter menos e o adversario mais)
    nb_empty = neighbours(empty)
    fr_p = popcount(p & nb_empty)
    fr_o = popcount(o & nb_empty)
    frontier = (fr_o - fr_p) / (fr_o + fr_p + 1.0)

    position = position_sum(p) - position_sum(o)
    danger = _danger(p, o)
    disc = popcount(p) - popcount(o)
    disc_w = DISC_SLOPE * max(0, 20 - empties)

    return (_lerp(*W['corner'], t) * corners
            + _lerp(*W['stable'], t) * stable
            + _lerp(*W['mobility'], t) * mobility
            + _lerp(*W['potmob'], t) * potmob
            + _lerp(*W['frontier'], t) * frontier
            + _lerp(*W['position'], t) * position
            + _lerp(*W['danger'], t) * danger
            + disc_w * disc)


def terminal_value(p, o):
    """Valor de um estado sem jogadas para ninguem: vitoria/derrota pela contagem de discos."""
    d = popcount(p) - popcount(o)
    if d > 0:
        return WIN_VALUE + d
    if d < 0:
        return -WIN_VALUE + d
    return 0
