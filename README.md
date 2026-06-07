# Agente de Análise Exploratória de Dados em Linguagem Natural

Trabalho Final — Tecnologia em Ciência de Dados (5º semestre) — Fatec Ourinhos

Esqueleto inicial do projeto. Os pontos marcados com `TODO` ao longo do código são onde
vocês devem completar a implementação.

---

## Visão geral

O projeto implementa um **agente conversacional** que recebe perguntas em português sobre
um arquivo CSV e responde executando, autonomamente, operações de análise exploratória
(EDA) por meio de *function calling*.

```
Usuário → Orquestrador → LLM (decide) → Tool (executa) → Observa → ... → Resposta
                              ↑___________________________________________|
                                        loop até resposta final
```

---

## Estrutura de pastas

```
projeto_agente_eda/
├── agent/                  # Loop do agente e integração com o LLM
│   ├── __init__.py
│   ├── agent.py            # Classe principal Agent
│   ├── llm_client.py       # Cliente da API (Anthropic / OpenAI / Ollama)
│   └── tool_registry.py    # Registro de tools disponíveis para o LLM
│
├── tools/                  # Implementação das ferramentas (pandas)
│   ├── __init__.py
│   ├── base.py             # Decorador @tool e base comum
│   ├── inspect_tools.py    # listar_colunas, descrever_dados, contar_valores
│   ├── filter_tools.py     # filtrar, agrupar_e_agregar
│   ├── stats_tools.py      # correlacao, detectar_outliers
│   └── plot_tools.py       # gerar_grafico
│
├── evaluation/             # Sistema de avaliação (benchmark)
│   ├── __init__.py
│   ├── benchmark.py        # Carrega benchmark.json e executa
│   ├── metrics.py          # Cálculo de acurácia, latência, custo, etc.
│   └── benchmark.json      # 5 perguntas de exemplo (vocês adicionam +25)
│
├── data/                   # CSV(s) usados pelo grupo (colocar aqui)
│   └── .gitkeep
│
├── outputs/                # Gráficos gerados pelo agente
│   └── .gitkeep
│
├── logs/                   # Logs de execução
│   └── .gitkeep
│
├── tests/                  # Testes unitários das tools
│   ├── __init__.py
│   └── test_tools.py
│
├── cli.py                  # Interface de linha de comando (entry point)
├── config.py               # Configurações centralizadas
├── requirements.txt        # Dependências
├── .env.example            # Exemplo de variáveis de ambiente (API keys)
├── .gitignore
└── README.md
```

---

## Instalação

### 1. Pré-requisitos

- Python 3.10 ou superior
- Conta em um provedor de LLM (Anthropic recomendado pela documentação clara)

### 2. Setup no PyCharm

1. **File → Open** e selecione a pasta do projeto.
2. PyCharm vai detectar `requirements.txt` e oferecer criar um virtualenv — aceite.
3. Após criar o venv, instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Copie `.env.example` para `.env` e preencha sua API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
5. **Marque a pasta raiz como Sources Root**: clique direito na pasta → *Mark Directory as → Sources Root*.

### 3. Coloque o CSV do grupo em `data/`

Por exemplo: `data/adult.csv`. Edite `config.py` para apontar para o arquivo.

---

## Como usar

### Modo interativo (CLI)

```bash
python cli.py
```

Exemplo de sessão:

```
> Quais são as colunas do dataset?
[O agente vai chamar listar_colunas() e responder]

> Qual a renda média por gênero?
[O agente vai chamar agrupar_e_agregar(grupo='sex', coluna='income', funcao='mean')]
```

### Rodar o benchmark completo

```bash
python -m evaluation.benchmark
```

Gera um relatório em `logs/benchmark_<timestamp>.json` com todas as métricas.

---

## O que vocês precisam completar

Procure por `TODO` no código. Os pontos principais são:

1. **`tools/`** — terminar a implementação das 8 tools obrigatórias.
2. **`agent/agent.py`** — completar o loop de raciocínio do agente.
3. **`evaluation/benchmark.json`** — criar pelo menos 25 perguntas adicionais.
4. **`evaluation/metrics.py`** — implementar comparação de respostas com gabarito.
5. **(Bônus)** — adicionar pelo menos 1 tool extra além das obrigatórias.

---

## Cronograma sugerido

Veja o enunciado do trabalho para o cronograma de 8 semanas.

---

## Política de uso de LLMs

Vocês PODEM usar ChatGPT/Claude/Copilot para programar.
Vocês NÃO PODEM entregar código que não compreendam.
Durante a apresentação, qualquer integrante pode ser questionado sobre qualquer linha.
