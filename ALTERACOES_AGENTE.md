# Alterações no agente de torneio (Othello)

## Problema

O `advsearch/your_agent/tournament_agent.py` original só sorteava uma entre quatro jogadas de abertura fixas.
A partir do segundo lance ele fazia jogadas ilegais, e o servidor desclassifica o jogador depois de
5 jogadas ilegais seguidas. Além disso, o tabuleiro do kit (`Board`) é lento: `copy()` converte o
tabuleiro inteiro em string e de volta, o que limita muito a profundidade de busca.

## O que foi alterado

### `advsearch/your_agent/tournament_agent.py` (reescrito)

| Mudança | Por quê |
|---|---|
| **Bitboards**: duas variáveis inteiras de 64 bits, uma por cor (bit = `y*8 + x`) | Geração de jogadas e viradas com operações de bits, sem copiar matrizes. É bem mais rápido que o `Board` do kit. |
| **Geração de jogadas** com preenchimento direcional nas 8 direções, desenrolado | É o ponto mais quente da busca; a versão desenrolada ficou cerca de 17% mais rápida. |
| **Negamax com poda alfa-beta e PVS** (busca com janela nula) | Poda mais galhos que o alfa-beta simples quando a ordenação de jogadas é boa. |
| **Aprofundamento iterativo** com orçamento de 4,0 s por jogada | O servidor dá 5 s e conta timeout como jogada ilegal. Sempre há uma jogada pronta da última profundidade completa; uma nova profundidade não começa se já passou 45% do tempo. |
| **Tabela de transposição** (dicionário indexado por `(P, O)`) | Reaproveita posições já avaliadas e fornece a melhor jogada anterior para ordenar primeiro. O hash de inteiros do Python substitui o Zobrist. |
| **Ordenação de jogadas**: jogada da tabela primeiro, depois as que deixam o adversário com menos jogadas e os cantos | Boa ordenação é o que faz a poda alfa-beta render. |
| **Final exato**: quando a profundidade alcança o número de casas vazias o resultado é exato; com 7 ou menos vazias usa um solver dedicado | No final da partida, a contagem real de peças é o que decide a vitória. |
| **Função de avaliação** específica de Othello | Ver a seção abaixo. |
| **Fallback de segurança**: qualquer erro na busca devolve uma jogada legal | Nunca perder a vez por um bug. |

### Função de avaliação

Calculada do ponto de vista de quem joga:

- **Mobilidade**: diferença de jogadas legais, com bônus ou penalidade quando um lado é obrigado a passar.
- **Cantos**: peso alto para cantos ocupados.
- **Estabilidade**: peças de borda contínuas a partir de um canto próprio não podem ser viradas.
- **X-squares e C-squares**: penalizados apenas enquanto o canto vizinho está vazio, porque é quando entregam o canto.
- **Fronteira**: peças vizinhas de casas vazias dão jogadas ao adversário e são penalizadas.
- **Fim de jogo** (20 ou menos casas vazias): a contagem de peças passa a pesar, e a paridade favorece quem faz o último lance.

Ter muitas peças no meio do jogo não é recompensado, porque isso costuma dar mobilidade ao adversário.

### Arquivos novos

- `test_tournament_agent.py`: testes de correção. Compara a geração de jogadas e as viradas com o `Board` do kit
  em 60 partidas aleatórias, testa uma posição com passe de vez e o limite de tempo.
- `bench_tournament.py`: roda partidas rápidas (sem o servidor) contra os jogadores aleatório, guloso e posicional
  e mostra vitórias, tempo médio e máximo por jogada, profundidade e nós por segundo.

## Resultados

| Teste | Resultado |
|---|---|
| Testes de correção | todos passam |
| 0,3 s por jogada, contra aleatório, guloso e posicional | 12 vitórias em 12 partidas, profundidade média 5,5 |
| Mesma busca, nossa avaliação contra a máscara posicional clássica | +10 de saldo em 12 partidas |
| `server.py` com 5 s por jogada, contra o aleatório | vitória por 51 a 0, sem timeouts nem jogadas ilegais |
| Orçamento de 4 s por jogada, 98 jogadas | média 2,70 s, máximo 4,135 s, profundidade média 6,8 |

## Como rodar

```
python -m unittest test_tournament_agent
python bench_tournament.py 4 0.3
python server.py othello advsearch/your_agent/tournament_agent.py advsearch/randomplayer/agent.py -d 5
```

O segundo comando recebe o número de partidas por adversário e os segundos por jogada.

## O que não foi feito

- Os arquivos obrigatórios do trabalho (`minimax.py`, `othello_minimax_*.py`, `mcts.py`) continuam como stubs,
  e os testes do kit para eles ainda falham.
- Não há livro de aberturas.
- O diretório continua com o nome `your_agent`; o README pede para renomeá-lo com o nome do agente.
- Se a máquina do torneio for mais lenta, reduza `TIME_LIMIT` em `tournament_agent.py` (por exemplo, para 3,5).
