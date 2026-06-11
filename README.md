# Agente Conversacional de Análise Exploratória de Dados com LLM


## Visão Geral

O projeto implementa um **agente conversacional** baseado em LLM que recebe perguntas em português sobre o dataset **F1 Race Results (2019–2024)** e responde executando, autonomamente, operações de análise exploratória (EDA) por meio de *function calling*.

A arquitetura adota o padrão **ReAct (Reasoning + Acting)**:

```
Usuário → Orquestrador → LLM (decide) → Tool (executa) → Observa → ... → Resposta
                              ↑___________________________________________|
                                        loop até resposta final (máx. 15 iterações)
```

---

## Dataset

**F1 Race Results** — resultados individuais de pilotos em corridas de Fórmula 1 das temporadas 2019 a 2024.

- Arquivo: `data/f1.csv`
- Registros: **2.559 linhas × 14 colunas**
- Fonte: [Kaggle — Formula 1 Race Results Dataset](https://www.kaggle.com)

| Coluna | Tipo | Descrição |
|---|---|---|
| Track | str | Nome do circuito |
| Position | int | Posição final (0 = não classificado) |
| Driver | str | Nome do piloto |
| Team | str | Nome da equipe |
| Starting Grid | int | Posição de largada no grid |
| Laps | int | Número de voltas completadas |
| Points | int | Pontos conquistados na corrida |
| +1 Pt | int | 1 se recebeu ponto extra pela volta mais rápida |
| season | int | Ano da temporada (2019–2024) |
| Set Fastest Lap | int | 1 se marcou a volta mais rápida da corrida |
| Status | int | 1=Finished, 2=NC, 3=DNF, 4=DNS, 5=DQ |
| Race Time | str | Tempo total de corrida (H:MM:SS.mmm ou +S.mmm) |
| Fastest Lap Time | str | Tempo da volta mais rápida (M:SS.mmm) |
| No | int | Número do carro |

---

## Estrutura de Pastas

```
projeto_agente_eda/
├── agent/                  # Loop do agente e integração com o LLM
│   ├── __init__.py
│   ├── agent.py            # Classe Agent com loop ReAct
│   ├── llm_client.py       # Cliente da API DeepSeek (compatível OpenAI)
│   └── tool_registry.py    # Registro dinâmico de tools
│
├── tools/                  # Implementação das ferramentas (pandas)
│   ├── __init__.py
│   ├── base.py             # Decorador @tool, TOOL_REGISTRY e DataState
│   ├── inspect_tools.py    # listar_colunas, descrever_dados, contar_valores
│   ├── filter_tools.py     # filtrar, filtrar_e_contar, agrupar_e_agregar,
│   │                       # analisar_tempo, tempo_total_piloto
│   ├── stats_tools.py      # correlacao, detectar_outliers
│   └── plot_tools.py       # gerar_grafico
│
├── evaluation/             # Sistema de avaliação (benchmark)
│   ├── __init__.py
│   ├── benchmark.py        # Carrega benchmark.json e executa avaliação
│   ├── metrics.py          # Cálculo de aprovação por palavras-chave, latência e custo
│   └── benchmark.json      # 30 perguntas (10 factuais, 15 analíticas, 5 ambíguas)
│
├── tests/                  # Testes unitários das tools
│   ├── __init__.py
│   └── test_tools.py       # 44 testes pytest em 6 classes
│
├── data/
│   └── f1_tratado.csv      # Dataset pré-processado
│
├── outputs/                # Gráficos gerados pelo agente (PNG)
├── logs/                   # Logs de execução e resultados de benchmark
├── cli.py                  # Interface de linha de comando (entry point)
├── config.py               # Configurações centralizadas (modelo, caminhos, limites)
├── requirements.txt        # Dependências
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore
└── README.md
```

---

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Conta na [API DeepSeek](https://api-docs.deepseek.com)

### Setup

1. Clone o repositório e crie um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Copie `.env.example` para `.env` e preencha sua chave:
   ```
   DEEPSEEK_API_KEY=sk-...
   ```

> O arquivo `data/f1_tratado.csv` já deve estar presente. O caminho é configurado em `config.py`.

---

## Como Usar

### Modo interativo (CLI)

```bash
python cli.py
```

Exemplo de sessão:

```
> Quais são as colunas do dataset?
[chama listar_colunas() e descreve as 14 colunas]

> Quem ganhou mais corridas em 2023?
[chama filtrar_e_contar("season==2023 and Position==1", "Driver")]
Max Verstappen — 19 vitórias em 22 corridas (86% de aproveitamento).

> Qual a correlação entre posição de largada e posição final?
[chama correlacao("Starting Grid", "Position", "pearson")]
Correlação de Pearson: 0,535 — positiva moderada.
```

### Comandos especiais da CLI

| Comando | Função |
|---|---|
| `/ajuda` | Lista todos os comandos disponíveis |
| `/trajetoria` | Exibe tool_calls e resultados da última pergunta |
| `/custo` | Mostra tokens consumidos, latência e custo estimado em USD |
| `/sair` | Encerra a sessão |

### Rodar o benchmark completo

```bash
python -m evaluation.benchmark
```

Gera um relatório em `logs/benchmark_<timestamp>.json` com todas as métricas.

### Rodar os testes unitários

```bash
pytest tests/test_tools.py -v
```

---

## Ferramentas Implementadas

São **11 ferramentas** distribuídas em 4 módulos. Todas recebem parâmetros simples (`str`, `int`) e retornam um dicionário serializável para JSON.

| Módulo | Ferramenta | Descrição |
|---|---|---|
| inspect | `listar_colunas()` | Lista nomes e tipos das 14 colunas do dataset |
| inspect | `descrever_dados()` | Estatísticas descritivas completas (média, desvio, quartis) |
| inspect | `contar_valores(coluna, top_n)` | Distribuição de frequência dos top-N valores de uma coluna |
| filter | `filtrar(condicao)` | Filtra com pandas query e retorna estatísticas do subconjunto |
| filter | `filtrar_e_contar(condicao, coluna)` | Filtra e conta ocorrências por coluna — ranking de vencedores |
| filter | `agrupar_e_agregar(grupo, col, func)` | GroupBy + agregação: sum, mean, min, max, count, median |
| filter | `analisar_tempo(coluna, op, cond)` | Converte Race Time / Fastest Lap Time para segundos e agrega |
| filter | `tempo_total_piloto(piloto, circ, ano)` | Retorna o tempo total de corrida de um piloto (absoluto ou calculado) |
| stats | `correlacao(col_a, col_b, metodo)` | Correlação de Pearson ou Spearman com interpretação textual |
| stats | `detectar_outliers(coluna, metodo)` | Outliers por IQR ou z-score: limites, contagem e exemplos |
| plot | `gerar_grafico(tipo, colunas, titulo)` | Histograma, boxplot, scatter ou barplot salvo em `outputs/` |

---

## Resultados do Benchmark

30 perguntas com gabaritos calculados diretamente via pandas.

| Categoria | Total | Aprovadas | Taxa | Tools (méd.) | Latência (méd.) |
|---|---|---|---|---|---|
| Factual | 10 | 10 | 100% | 2,1 | 6,1 s |
| Analítica | 15 | 13 | 87% | 2,1 | 6,2 s |
| Ambígua | 5 | 5 | 100% | 7,2 | 16,1 s |
| **TOTAL** | **30** | **28** | **93%** | **2,8** | **7,8 s** |

Custo total estimado de US$ 0,09 por execução completa do benchmark.

---

## Provedor de LLM

O agente utiliza o modelo **`deepseek-chat`** via [API DeepSeek](https://api-docs.deepseek.com), que é compatível com o formato da API OpenAI. A biblioteca `openai` é usada como cliente.