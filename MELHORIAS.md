# Melhorias no agente de torneio (versao 2)

Arquivo principal: `advsearch/delfos/tournament_agent.py` (a versao anterior foi mantida em `tournament_agent_v1.py`).

## Alteracoes
- `advsearch/delfos/bitboard.py` (novo): motor de bitboards. Geracao de jogadas, viradas e estabilidade por deslocamentos de bits, em vez de varredura de casas. Verificado contra um motor de referencia em ~18 mil posicoes.
- `advsearch/delfos/othello_eval.py` (novo): avaliacao por fases (abertura -> final) com cantos, discos estaveis, mobilidade, mobilidade potencial, fronteira, tabela posicional (Hasegawa) e penalidade por X/C com canto vazio.
- `advsearch/delfos/tournament_agent.py`: negamax com alfa-beta, aprofundamento iterativo, tabela de transposicao; passes nao consomem profundidade, entao o final e' buscado ate o fim.

## Desempenho (medido)
- Velocidade: ~34-44 mil nos/s (antes ~9-20 mil) em posicoes de meio-jogo.

## Ainda nao validado
- Nao ha resultado comparativo de forca (agente novo x antigo) concluido. Os pesos da avaliacao sao iniciais e nao foram ajustados experimentalmente.
