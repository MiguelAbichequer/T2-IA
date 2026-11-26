"""
Motor de bitboards para Othello.

Representacao: cada cor e' um inteiro de 64 bits. O bit i corresponde a casa
(x = i % 8, y = i // 8), ou seja, x e' a coluna e y e' a linha, igual a
Board.tiles[y][x] e as jogadas (x, y) do projeto.

Todas as funcoes trabalham em termos de (p, o): p = bits do jogador que
move, o = bits do adversario. Isso permite busca negamax sem distinguir cores.

Por que existe: a versao anterior gerava jogadas legais varrendo o tabuleiro
casa a casa com listas e copiava estados por string. Aqui as operacoes sao
deslocamentos e mascaras de bits, o que reduz o custo por no' em uma ordem de
grandeza (ver benchmarks em relatorio).
"""

FULL = (1 << 64) - 1
COL0 = sum(1 << (8 * y) for y in range(8))      # x = 0
COL7 = COL0 << 7                                # x = 7
ROW0 = 0xFF                                     # y = 0
ROW7 = 0xFF << 56                               # y = 7
NOT_COL0 = FULL & ~COL0
NOT_COL7 = FULL & ~COL7
EDGES = ROW0 | ROW7 | COL0 | COL7
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# direcoes (dx, dy): x cresce para a direita, y para baixo
DIRS = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0)]

try:
    popcount = int.bit_count                    # Python >= 3.10
except AttributeError:                          # pragma: no cover
    def popcount(v):
        return bin(v).count("1")


# (deslocamento em bits, mascara) por direcao: s > 0 e' deslocamento a esquerda, s < 0 a direita.
_SHIFTS = []
for _dx, _dy in DIRS:
    _s = _dy * 8 + _dx
    _mask = NOT_COL0 if _dx == 1 else (NOT_COL7 if _dx == -1 else FULL)
    _SHIFTS.append((_s, _mask))


def shift(b, dx, dy):
    """Desloca todos os bits de b uma casa na direcao (dx, dy), sem 'dar a volta' no tabuleiro."""
    s = dy * 8 + dx
    b = (b << s) & FULL if s > 0 else b >> -s
    if dx == 1:
        return b & NOT_COL0
    if dx == -1:
        return b & NOT_COL7
    return b


def neighbours(b):
    """Casas adjacentes (8 direcoes) a qualquer casa de b."""
    r = 0
    for s, mask in _SHIFTS:
        r |= ((b << s) & mask) if s > 0 else ((b >> -s) & mask)
    return r


def legal_moves(p, o):
    """Bitboard das jogadas legais de p (contra o)."""
    empty = FULL & ~(p | o)
    moves = 0
    for s, mask in _SHIFTS:
        # a partir de cada peca de p, percorre uma sequencia de pecas de o
        if s > 0:
            t = (p << s) & mask & o
            while t:
                moves |= (t << s) & mask & empty
                t = (t << s) & mask & o
        else:
            s = -s
            t = (p >> s) & mask & o
            while t:
                moves |= (t >> s) & mask & empty
                t = (t >> s) & mask & o
    return moves


def flips(p, o, move_bit):
    """Bitboard das pecas de o capturadas pela jogada em move_bit (p e' quem joga)."""
    f = 0
    for s, mask in _SHIFTS:
        line = 0
        if s > 0:
            t = (move_bit << s) & mask
            while t & o:
                line |= t
                t = (t << s) & mask
        else:
            ss = -s
            t = (move_bit >> ss) & mask
            while t & o:
                line |= t
                t = (t >> ss) & mask
        if t & p:
            f |= line
    return f


def apply_move(p, o, move_bit):
    """Retorna (novo_p, novo_o) apos a jogada; novo_p e' quem acabou de jogar."""
    f = flips(p, o, move_bit)
    return p | move_bit | f, o & ~f


def stable_discs(p, o):
    """
    Discos estaveis de p (que nunca poderao ser virados), aproximacao conservadora.

    Um disco e' estavel se, em cada um dos 4 eixos (horizontal, vertical e as
    duas diagonais), ou ele esta na borda do tabuleiro naquele eixo, ou um dos
    vizinhos nesse eixo e' outro disco estavel de p. Comecamos pelos cantos
    (sempre estaveis) e propagamos ate o ponto fixo. Isto e' a ideia de
    'estabilidade' de Lazard (mais precisamente: discos ancorados em cantos).
    """
    s = p & CORNERS
    if not s:
        return 0
    while True:
        # os 8 deslocamentos abaixo trazem, para cada casa, o estado de cada vizinho
        e = (s << 1) & NOT_COL0      # vizinho a oeste estavel
        w = (s >> 1) & NOT_COL7      # vizinho a leste estavel
        n = s >> 8                   # vizinho a sul estavel
        so = (s << 8) & FULL         # vizinho a norte estavel
        ne = (s >> 7) & NOT_COL0     # vizinho a sudoeste estavel
        sw = (s << 7) & NOT_COL7     # vizinho a nordeste estavel
        nw = (s >> 9) & NOT_COL7     # vizinho a sudeste estavel
        se = (s << 9) & NOT_COL0     # vizinho a noroeste estavel
        h = COL0 | COL7 | e | w
        v = ROW0 | ROW7 | n | so
        d1 = EDGES | ne | sw
        d2 = EDGES | nw | se
        new = s | (p & h & v & d1 & d2)
        if new == s:
            return s
        s = new


def to_bits(tiles, color):
    """Converte a matriz tiles (lista de linhas, 'B'/'W'/'.') em bitboard de color."""
    bits = 0
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if t == color:
                bits |= 1 << (y * 8 + x)
    return bits


def bit_to_xy(bit_index):
    """Indice de bit -> (x, y) usado pelo projeto (coluna, linha)."""
    return bit_index % 8, bit_index // 8


def from_gamestate(state):
    """(p, o) a partir de um GameState do projeto (p = quem joga)."""
    tiles = state.board.tiles
    mine = state.player
    theirs = 'W' if mine == 'B' else 'B'
    return to_bits(tiles, mine), to_bits(tiles, theirs)
