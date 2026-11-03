# Resultados da avaliação (para o relatório)

Rodado em 03/11/2026, branch `othello-heuristicas`, Windows 11.

## Tic-Tac-Toe Misère

| Pergunta | Resultado |
|---|---|
| 1. Sempre ganha ou empata contra o randomplayer? | **Sim.** 200 partidas: como pretas (começa) 65 vitórias e 35 empates; como brancas 100 vitórias. Nenhuma derrota. |
| 2. Sempre empata consigo mesmo? | **Sim.** minimax × minimax termina em empate (o jogo é determinístico, então toda repetição é igual). |
| 3. Não perde para um humano com a melhor estratégia? | **Sim.** Testamos o minimax contra *todas* as sequências possíveis de jogadas do oponente (cobre qualquer estratégia humana): o pior caso é empate, jogando de pretas (584 ramos do oponente) ou de brancas (1647 ramos). |

Os testes `test_minimax_tttm.py` (incluindo `test_perfect_play`) também passam.

## Othello — mini-torneio (server.py, `-d 5`, profundidade fixa 4)

| Partida (pretas × brancas) | Placar | Vencedor |
|---|---|---|
| Contagem × Posicional | 28 × 36 | Posicional |
| Posicional × Contagem | 22 × 42 | Contagem |
| Contagem × Customizada | 12 × 52 | Customizada |
| Customizada × Contagem | 56 × 8 | Customizada |
| Posicional × Customizada | 21 × 43 | Customizada |
| Customizada × Posicional | 46 × 18 | Customizada |

| Agente | Vitórias | Peças somadas |
|---|---|---|
| **Customizada** | **4** | **197** |
| Posicional | 1 | 97 |
| Contagem | 1 | 90 |

Mais bem-sucedida: **heurística customizada** (4 de 4 vitórias). Nenhuma jogada ilegal nem estouro de tempo.

## Extras (script direto, sem server.py)

| Partida (pretas × brancas) | Placar |
|---|---|
| Torneio × Customizada | 54 × 10 |
| Customizada × Torneio | 20 × 44 |
| Torneio × Posicional | 63 × 1 |
| Contagem × Torneio | 5 × 59 |
| Torneio (novo) × Torneio (sem tabela de transposição) | 54 × 10 |
| Torneio (sem TT) × Torneio (novo) | 18 × 46 |
| MCTS × Customizada | 16 × 48 |
| Customizada × MCTS | 48 × 16 |
| MCTS × Contagem | 34 × 30 |
| Posicional × MCTS | 28 × 36 |
| Torneio × random (server.py) | 63 × 1 |

MCTS no tttm: 6 de 6 vitórias contra o random (1 s por jogada).
