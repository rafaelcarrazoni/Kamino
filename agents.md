User: explique o fluxo do código considerando a execucao de src.main

GitHub Copilot: Vou mapear a entrada real do projeto e seguir o caminho de execução a partir de src.main para explicar o fluxo de forma precisa.

Searched for regex `src\.main|from src|import src|if __name__ == ['\"]__main__['\"]` (`**/*.py`), 197 results

Read 

Read 

Read , lines 1 to 260

Read , lines 1 to 220

Read , lines 1 to 220

Read , lines 1 to 220

Read , lines 1 to 220

Encontrei o ponto exato: o módulo principal do pipeline está em `main.py`, e ele orquestra uma sequência de passos de normalização, geração, filtragem, reparo, clustering e seleção de configurações. Vou fechar com o mapa do fluxo e o papel de cada etapa.

Read , lines 1 to 220

Read 

Searched for regex `def startup\s*\(` (`**/pipeline/src/**/*.py`), 1 result

Read , lines 720 to 820

## Fluxo da execução a partir de `src.main`

O ponto de entrada real do pipeline está em `main.py`. Quando esse módulo é executado, o bloco final:

```python
if __name__ == "__main__":
    main()
```

chama a função `main()`, que orquestra toda a pipeline.

---

## 1) Inicialização e configuração

No topo de `main.py`, o código importa:

- `config.py`: concentra todos os caminhos, thresholds, modelos, prompts e configurações globais.
- módulos de etapas em `steps`: `normalization`, `clone_gen`, `filtering`, `reprompt`, `clustering`
- utilitários em `utils`

A primeira chamada dentro de `main()` é:

```python
startup()
```

Essa função apenas imprime o banner e mensagem inicial do projeto; ela não executa processamento pesado.

---

## 2) Etapa 1: normalização

Em `main.py`, o fluxo verifica se o dataset filtrado já existe:

```python
if (not os.path.exists(FILTERED_DATASET_PATH)):
    nz.pre_process_data()
else:
    print("Dataset files already exist. Skipping Step 1.")
```

A lógica real está em `normalization.py`:

- carrega o dataset bruto
- normaliza entradas para um formato uniforme (`id`, `original_code`, `test`, `description`, `metadata`)
- salva em `DATASET_PATH`
- executa testes do código original com `validate_with_unittest`
- filtra entradas fáceis/difíceis e gera o dataset de entrada para geração de clones

Ou seja, nessa etapa o código prepara a base de dados que será usada depois pela geração de clones.

---

## 3) Etapa 2: geração de clones

Depois da normalização, o fluxo chama:

```python
cg.run_generation()
```

em `clone_gen.py`.

Essa função faz o seguinte:

- valida conexão com Ollama
- verifica se já existem combinações geradas
- monta combinações de modelos, contextos e estratégias
- para cada configuração, gera clones a partir do dataset usando LLM
- extrai o código do retorno do modelo
- força o nome da função para `task_func`
- salva os resultados em arquivos como `OUT_PATH`

Em resumo: a geração é o “ponto em que o modelo cria variações de código a partir do dataset”.

---

## 4) Etapa 3: filtro por CodeBLEU

A sequência continua com:

```python
fl.run_codebleu_filtering()
```

em `filtering.py`.

Esse passo:

- limpa e separa os clones gerados
- calcula CodeBLEU entre o código original e cada clone
- mantém apenas clones com similaridade aceitável
- salva no arquivo de saída de filtro por CodeBLEU

A métrica é controlada por `CODEBLEU_THRESHOLD` em `config.py`.

---

## 5) Etapa 4: execução de testes

Depois do filtro por similaridade, o código executa:

```python
fl.run_tests()
```

Ainda em `filtering.py`.

Aqui, cada clone é executado contra os testes do problema, usando a função `validate_with_unittest` de `helper_functions.py`. Essa função:

- monta um arquivo temporário com o código em teste + testes
- executa em subprocesso
- retorna um dicionário de resultado por teste (`PASS`, `FAIL`, `ERROR`)

Essa etapa decide quais clones são funcionalmente válidos.

---

## 6) Etapa 5: reprompt / correção dos clones

Depois, o pipeline chama:

```python
rp.run_reprompt()
```

em `reprompt.py`.

Essa parte:

- pega clones que passaram em parte dos testes
- considera `MIN_TEST_REPROMPT` como critério
- identifica testes falhando
- envia o código e os erros para o modelo novamente
- tenta regenerar uma versão melhorada
- salva em `REPROMPT_PATH`

É uma etapa de “refinamento” dos clones que já estavam quase corretos.

---

## 7) Etapa 6: filtro final por testes

Em seguida:

```python
fl.run_test_filtering()
```

Esse passo combina:

- resultados originais
- clones repromptados
- análise final de CodeBLEU e testes

e produz a base refinada. Ou seja, ele remove clones que não sobreviveram às validações finais.

---

## 8) Etapa 7: clustering

Depois:

```python
cl.run_clustering()
```

em `clustering.py`.

Aqui o código:

- monta uma matriz de similaridade entre clones
- usa CodeBLEU como distância/afinidade
- aplica aglomerative clustering
- escolhe representantes por cluster
- salva o dataset final em `FINAL_DATASET`

Essa etapa serve para reduzir redundância: se vários clones são muito parecidos, mantém só um representante de cada cluster.

---

## 9) Etapa final: seleção das melhores configurações

Por fim, em `main.py`:

```python
select_top_n_configs()
```

Essa função, em `efficiency.py`, mede a eficiência de cada combinação de:

- modelo
- contexto
- refatoração
- estratégia

A partir de dados em vários estágios do pipeline, ela calcula qual configuração produz melhor relação entre custo e sobrevivência até o final, e salva em `top_configs.json`.

---

## Visão geral do fluxo

Em uma linha, o pipeline faz:

1. normaliza dataset
2. gera clones com LLM
3. remove clones pouco semelhantes
4. testa cada clone
5. reprompta casos quase válidos
6. filtra por resultados reais
7. agrupa clones similares
8. seleciona as melhores configurações

---

## Ponto central da arquitetura

O que torna esse código funcionar bem é o padrão de orquestração do `main()`: cada etapa é uma função separada, toda a configuração fica centralizada em `config.py`, e o fluxo é guiado por arquivos JSON de saída intermediários.

Se quiser, posso continuar com uma explicação mais “linha a linha” de `main.py`, ou fazer um diagrama de execução em formato de fluxo.

User: Quais são as opções de refatoração (contextos, refacs e estrategias) possiveis. 

GitHub Copilot: Vou olhar diretamente as definições de configuração para listar exatamente quais combinações o projeto aceita e como elas são usadas no fluxo de geração.

Read , lines 40 to 120

Read , lines 1 to 130

Searched for regex `refac_|zero-shot|contexts|STRATEGIES|REFACS|context_builders` (`**/*.{py,md}`), 368 results

Read , lines 1 to 220

Read , lines 160 to 260

Read , lines 1 to 120

## Opções de refatoração suportadas

O projeto define a combinação de configuração como:
(model, context, strategy, refactorings)

Conforme `config.py:61-75`, o arquivo de configuração atual está com valores bem restritos:

- contextos: `["code"]`
- refacs: `[]`
- estratégias: `["zero-shot"]`

Mas as opções possíveis no design do projeto são as seguintes.

### 1) Contextos possíveis
Segundo `step2.md:32-44`, os contextos aceitos são:

- `code` → apenas a função original
- `tests` → apenas os testes
- `complete` → código + testes
- `AST` → árvore de sintaxe abstrata

> Os contextos são mutuamente exclusivos, como explica o próprio documento.

---

### 2) Refatorações possíveis
As refatorações estão definidas em `prompts.py:29-57` e são:

- `refac_1` — algoritmo diferente
- `refac_2` — troca de biblioteca/API
- `refac_3` — mudança de estrutura de dados
- `refac_4` — variação de estilo/formatação
- `refac_5` — isolamento de efeitos colaterais
- `refac_6` — robustez/segurança
- `refac_7` — “bad smells” / código menos elegante

Essas refatorações são combinadas, e o código usa isso em `run_generation()` em `clone_gen.py:18-53`.

---

### 3) Estratégias possíveis
As estratégias também ficam em `prompts.py:175-220`:

- `zero-shot` — instrução direta, pouco guia
- `cot` — Chain-of-Thought, pede raciocínio em etapas

O documento de configuração também reforça isso em `step2.md:45-63`.

---

## Resumo prático

No projeto, a configuração “ideal” de experimentação é algo como:

- contextos: `code | tests | complete | AST`
- estratégias: `zero-shot | cot`
- refacs: qualquer combinação de `refac_1..refac_7`

Mas o arquivo atual de execução em `config.py:61-75` está bem mais enxuto, com apenas:

- contexto: `code`
- estratégia: `zero-shot`
- refac: vazio

Isso significa que a pipeline está configurada para uma execução mais simples e menor, e não para a matriz completa do paper.

Se quiser, posso te mostrar exatamente como essas opções são montadas em uma combinação real, por exemplo:
`(gemma3:latest, code, zero-shot, [refac_1, refac_4, refac_5])`.

User: Explique combinations per set e num_combinations_touse. alem disso tenho uma duvida: essas três configurações definem quantas vezes a pipeline vai tentar gerar os clones ou a cada tentativa de gerar ela vai escolher uma combinação aleatoria e rodar? 

GitHub Copilot: Vou explicar exatamente o efeito dessas duas variáveis no loop de geração e como elas interagem com o sorteio das combinações no código.

Read , lines 18 to 120

Searched for regex `def _select_balanced_combinations|def _load_used_combinations|def _run_clone_generation` (`**/pipeline/src/steps/*.py`), 3 results

Read , lines 220 to 402

## Entendendo `COMBINATIONS_PER_SET` e `NUM_COMBINATIONS_TOUSE`

Essas duas variáveis controlam quantas combinações de refatorações a pipeline vai considerar antes de disparar a geração de clones.

O ponto exato está em `clone_gen.py:18-53`:

- `all_combinations = list(combinations(REFACS, COMBINATIONS_PER_SET))`
- `subset_combinations = _select_balanced_combinations(all_combinations, NUM_COMBINATIONS_TOUSE, REFACS, RANDOM_SEED)`

E as definições atuais estão em `config.py:61-75`:

- `CONTEXTS = ["code", "tests"]`
- `REFACS = [f"refac_{i}" for i in range(1, 8)]`
- `STRATEGIES = ["zero-shot"]`
- `COMBINATIONS_PER_SET = 1`
- `NUM_COMBINATIONS_TOUSE = 1`

---

### 1) `COMBINATIONS_PER_SET`

Esse valor define o tamanho de cada conjunto de refatorações que será testado.

No seu caso:

```python
REFACS = ["refac_1", "refac_2", ..., "refac_7"]
COMBINATIONS_PER_SET = 1
```

Então a pipeline cria todas as combinações de tamanho 1:

- `("refac_1",)`
- `("refac_2",)`
- ...
- `("refac_7",)`

Ou seja, ela está testando uma refac por vez, e não combina 2 ou 3 ao mesmo tempo.

Se fosse:

```python
COMBINATIONS_PER_SET = 2
```

ela criaria combinações como:

- `("refac_1", "refac_2")`
- `("refac_1", "refac_3")`
- ...
- `("refac_6", "refac_7")`

---

### 2) `NUM_COMBINATIONS_TOUSE`

Esse valor define quantas dessas combinações geradas serão realmente usadas no experimento.

No seu caso:

```python
NUM_COMBINATIONS_TOUSE = 1
```

então, dentre todas as combinações possíveis de tamanho 1, a função `_select_balanced_combinations()` escolhe apenas 1 combinação para usar.

O código em `clone_gen.py:331-373` faz esse sorteio “balanceado”, não totalmente aleatório puro, para evitar que uma refac seja usada demais.

---

## Então, quantas vezes ela gera?

A resposta é:

- Não é “uma geração aleatória por clone”.
- É “para cada configuração (modelo, strategy, context, refac-set), a pipeline executa o gerador várias vezes”.

O loop real é:

```python
for model in ALL_MODELS:
    for strategy in STRATEGIES:
        for context in CONTEXTS:
            for refac_tuple in subset_combinations:
                _run_clone_generation(...)
```

Dentro de `_run_clone_generation()` em `clone_gen.py:253-329`, ele faz:

```python
for k in range(clones_per_entry):
    ... gera um clone ...
```

e `CLONES_PER_ENTRY` está em `config.py:58-60` como 20 no seu arquivo atual.

Então, com a sua configuração atual:

- 2 modelos
- 1 strategy
- 2 contexts
- 1 refac selecionada

Total de configurações:

2 × 1 × 2 × 1 = 4

Cada configuração gera:

20 clones por entrada

Logo, a pipeline tenta gerar 4 configurações, e cada uma pode produzir 20 clones por item do dataset.

---

## Resposta direta à sua dúvida

> Essas três configurações definem quantas vezes a pipeline vai tentar gerar os clones ou a cada tentativa de gerar ela vai escolher uma combinação aleatoria e rodar?

Na prática:

- `CONTEXTS`, `STRATEGIES`, `REFACS` definem o espaço de possibilidades.
- `COMBINATIONS_PER_SET` define o tamanho da combinação de refac.
- `NUM_COMBINATIONS_TOUSE` define quantas combinações daquele espaço serão usadas.
- A escolha da combinação não acontece em cada clone individual; ela acontece antes do laço principal de geração, em um passo de seleção.
- Depois disso, para cada configuração escolhida, o código gera `CLONES_PER_ENTRY` clones usando essa mesma combinação.

Em outras palavras:

- não é “sorteia uma combinação nova para cada clone”
- é “sorteia/seleciona um conjunto de refatorações uma vez para cada configuração de geração, e então gera vários clones com esse mesmo conjunto”

Se quiser, posso te mostrar um cálculo exato do número total de execuções para o seu arquivo atual, usando:
`ALL_MODELS`, `CONTEXTS`, `STRATEGIES`, `REFACS`, `COMBINATIONS_PER_SET`, `NUM_COMBINATIONS_TOUSE`, `CLONES_PER_ENTRY`.

User: o calculo de métricas está funcionando? 

GitHub Copilot: Vou checar o código que calcula CodeBLEU e os pontos de uso da métrica no fluxo para confirmar se o pipeline realmente usa a métrica corretamente e se há algum risco de falha.

Checked , , , no problems found

Searched for text `calc_complete_codebleu|calc_syntactic_codebleu|CodeBLEU|codebleu` (`**/pipeline/src/**/*.py`), 106 results

Ran terminal command:  cd /Users/rafaelcarrazoni/Documents/luc/Kamino && python - <<'PY'
from pipeline.src.utils.helper_functions import calc_complete_codebleu, calc_syntactic_codebleu

a = "def task_func(x):\n    return x + 1\n"
b = "def task_func(x):\n    return x + 1\n"
c = "def task_func(x):\n    return x * 2\n"

print('complete_same=', calc_complete_codebleu(a, b, lang='python'))
print('complete_diff=', calc_complete_codebleu(a, c, lang='python'))
print('syntactic_same=', calc_syntactic_codebleu(a, b, lang='python'))
print('syntactic_diff=', calc_syntactic_codebleu(a, c, lang='python'))
PY

A primeira verificação falhou por ambiente: o comando `python` não existe aqui. Vou repetir com o interpretador correto para confirmar a métrica de fato.

Ran terminal command:  cd /Users/rafaelcarrazoni/Documents/luc/Kamino && python3 - <<'PY'
from pipeline.src.utils.helper_functions import calc_complete_codebleu, calc_syntactic_codebleu

a = "def task_func(x):\n    return x + 1\n"
b = "def task_func(x):\n    return x + 1\n"
c = "def task_func(x):\n    return x * 2\n"

print('complete_same=', calc_complete_codebleu(a, b, lang='python'))
print('complete_diff=', calc_complete_codebleu(a, c, lang='python'))
print('syntactic_same=', calc_syntactic_codebleu(a, b, lang='python'))
print('syntactic_diff=', calc_syntactic_codebleu(a, c, lang='python'))
PY

Read 

## Status da métrica

Não, no ambiente atual o cálculo de métricas não está funcionando.

### Evidência
Eu executei a verificação direta da função de CodeBLEU e o resultado foi:

```bash
cd /Users/rafaelcarrazoni/Documents/luc/Kamino && python3 - <<'PY'
from pipeline.src.utils.helper_functions import calc_complete_codebleu, calc_syntactic_codebleu
...
PY
```

e a saída foi:

```text
ModuleNotFoundError: No module named 'parso'
```

Ou seja, o código que calcula a métrica existe e está conectado no pipeline, mas a execução falha antes de chegar ao cálculo por falta de dependência.

---

## Onde o cálculo está sendo usado

A lógica está em:

- `helper_functions.py`
- `filtering.py`
- `clustering.py`

Em especial:

- `calc_complete_codebleu(...)` é usado para comparar clone vs. código original
- `calc_syntactic_codebleu(...)` é usado para comparar clone vs. clone no clustering

Então a implementação está “planejada” e integrada corretamente; o que está quebrado no momento é o ambiente de execução.

---

## O que precisa ser feito

O projeto declara essa dependência em `requirements.txt`, incluindo `parso`. Então o próximo passo é instalar deps do projeto:

```bash
cd /Users/rafaelcarrazoni/Documents/luc/Kamino/pipeline
pip install -r requirements.txt
```

ou, se quiser só a dependência faltante:

```bash
pip install parso
```

> Depois disso, a métrica pode funcionar normalmente, mas ainda vale testar um caso simples de código igual vs. diferente para confirmar o comportamento real.

Se quiser, posso te ajudar a rodar essa validação final depois da instalação e te dizer se a métrica está discriminando corretamente clones semelhantes vs. diferentes.

User: tenta agora

GitHub Copilot: Ran terminal command:  cd /Users/rafaelcarrazoni/Documents/luc/Kamino && python3 -m pip install parso >/tmp/kamino_pip.log 2>&1 && python3 - <<'PY'
from pipeline.src.utils.helper_functions import calc_complete_codebleu, calc_syntactic_codebleu

a = "def task_func(x):\n    return x + 1\n"
b = "def task_func(x):\n    return x + 1\n"
c = "def task_func(x):\n    return x * 2\n"

print('complete_same=', calc_complete_codebleu(a, b, lang='python'))
print('complete_diff=', calc_complete_codebleu(a, c, lang='python'))
print('syntactic_same=', calc_syntactic_codebleu(a, b, lang='python'))
print('syntactic_diff=', calc_syntactic_codebleu(a, c, lang='python'))
PY

Vou confirmar com uma checagem explícita do ambiente: primeiro importando as dependências, depois executando a métrica. Isso elimina qualquer ambiguidade sobre se a instalação foi bem-sucedida.

Ran terminal command:  cd /Users/rafaelcarrazoni/Documents/luc/Kamino && python3 - <<'PY'
import sys
mods = ['parso', 'codebleu']
for m in mods:
    try:
        __import__(m)
        print(m, 'OK')
    except Exception as e:
        print(m, 'FAIL', type(e).__name__, e)

from pipeline.src.utils.helper_functions import calc_complete_codebleu, calc_syntactic_codebleu

a = "def task_func(x):\n    return x + 1\n"
b = "def task_func(x):\n    return x + 1\n"
c = "def task_func(x):\n    return x * 2\n"

print('complete_same=', calc_complete_codebleu(a, b, lang='python'))
print('complete_diff=', calc_complete_codebleu(a, c, lang='python'))
print('syntactic_same=', calc_syntactic_codebleu(a, b, lang='python'))
print('syntactic_diff=', calc_syntactic_codebleu(a, c, lang='python'))
print('EXIT=0')
PY

## Resultado da tentativa

Ainda não está funcionando.

A verificação executada mostrou isso de forma explícita:

- `parso FAIL ModuleNotFoundError No module named 'parso'`
- `codebleu FAIL ModuleNotFoundError No module named 'codebleu'`

e a importação do módulo que calcula a métrica falha em `helper_functions.py` por causa disso.

> Isso significa que o ambiente Python em uso não tem as dependências declaradas em `requirements.txt`, então o cálculo de CodeBLEU nunca chega a rodar.

---

## O que está quebrado

O problema não é o código da métrica em si; o problema é o ambiente:

- `helper_functions.py` importa `parso`
- a biblioteca `codebleu` também é necessária
- ambas faltam no ambiente atual

---

## Próximo passo correto

Instalar as dependências do projeto no mesmo ambiente Python que está rodando a pipeline:

```bash
cd /Users/rafaelcarrazoni/Documents/luc/Kamino
python3 -m pip install -r pipeline/requirements.txt
```

Se quiser, posso continuar e te ajudar a validar o ambiente correto para o projeto (venv vs sistema Python), porque isso é o que está impedindo a métrica de funcionar agora.