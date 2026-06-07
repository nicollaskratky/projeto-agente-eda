"""
Configurações centralizadas do projeto.

Tudo que pode variar entre execuções (caminhos, modelo, limites) fica aqui.
Assim os alunos não precisam caçar valores espalhados pelo código.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env automaticamente
load_dotenv()

# ============================================================
# CAMINHOS
# ============================================================
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data"
OUTPUTS_DIR = ROOT_DIR / "outputs"
LOGS_DIR = ROOT_DIR / "logs"
EVAL_DIR = ROOT_DIR / "evaluation"

# Garante que as pastas existem
for d in [DATA_DIR, OUTPUTS_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)

# ============================================================
# DATASET
# ============================================================
# TODO: alterar para o arquivo CSV do seu grupo.
DATASET_PATH = DATA_DIR / "exemplo.csv"

# ============================================================
# LLM
# ============================================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5")

# Chaves de API (lidas do .env)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ============================================================
# AGENTE
# ============================================================
# Quantas iterações no máximo o agente pode fazer antes de desistir.
# Evita loops infinitos quando o agente fica confuso.
MAX_AGENT_ITERATIONS = 10

# Quantos tokens no máximo o LLM pode gerar por resposta.
MAX_TOKENS_PER_RESPONSE = 1024

# ============================================================
# AVALIAÇÃO
# ============================================================
BENCHMARK_FILE = EVAL_DIR / "benchmark.json"

# Tolerância numérica para considerar duas respostas iguais
# (ex.: 100.0 e 100.001 devem ser tratadas como iguais)
NUMERIC_TOLERANCE = 1e-2
