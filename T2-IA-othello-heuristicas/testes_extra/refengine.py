"""Motor de referencia independente (ingenuo, mas obviamente correto) para validar as regras.
Convencao: tabuleiro grid[row][col], 'B' preto, 'W' branco, '.' vazio.
Jogadas expostas como (x=col, y=row), igual ao projeto."""
DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def initial():
    g = [['.']*8 for _ in range(8)]
    g[3][3]='W'; g[3][4]='B'; g[4][3]='B'; g[4][4]='W'
    return g

def flips(g, r, c, p):
    o = 'W' if p=='B' else 'B'
    out = []
    for dr, dc in DIRS:
        line = []
        rr, cc = r+dr, c+dc
        while 0<=rr<8 and 0<=cc<8 and g[rr][cc]==o:
            line.append((rr,cc)); rr+=dr; cc+=dc
        if line and 0<=rr<8 and 0<=cc<8 and g[rr][cc]==p:
            out.extend(line)
    return out

def legal(g, p):
    res = set()
    for r in range(8):
        for c in range(8):
            if g[r][c]=='.' and flips(g,r,c,p):
                res.add((c,r))
    return res

def play(g, x, y, p):
    f = flips(g, y, x, p)
    assert f, "jogada ilegal"
    g = [row[:] for row in g]
    g[y][x] = p
    for r,c in f: g[r][c] = p
    return g

def score(g):
    b = sum(row.count('B') for row in g); w = sum(row.count('W') for row in g)
    return b, w

def next_player(g, p):
    o = 'W' if p=='B' else 'B'
    if legal(g,o): return o
    if legal(g,p): return p
    return None
