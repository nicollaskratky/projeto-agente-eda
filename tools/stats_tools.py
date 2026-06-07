"""
Ferramentas estatísticas: correlação e detecção de outliers.

TODO (alunos):
  - A função detectar_outliers tem apenas o método IQR implementado.
    Adicionem o método z-score como exercício.
  - Considerem se faz sentido adicionar uma tool de teste de hipótese
    (ex.: teste t, qui-quadrado) como tool EXTRA para pontuar no bônus.
"""

import numpy as np
import pandas as pd
from .base import tool, state


# ============================================================
# correlacao
# ============================================================

@tool(
    description=(
        "Calcula a correlação entre duas colunas numéricas. "
        "Aceita método Pearson (linear) ou Spearman (monotônica/ordinal)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna_a": {"type": "string"},
            "coluna_b": {"type": "string"},
            "metodo": {
                "type": "string",
                "enum": ["pearson", "spearman"],
                "description": "Método de correlação (default: pearson).",
            },
        },
        "required": ["coluna_a", "coluna_b"],
    },
)
def correlacao(coluna_a: str, coluna_b: str, metodo: str = "pearson") -> dict:
    """Correlação entre duas colunas numéricas."""
    df = state.require_loaded()

    # Validações
    for col in (coluna_a, coluna_b):
        if col not in df.columns:
            return {"erro": f"Coluna '{col}' não existe."}
        if not pd.api.types.is_numeric_dtype(df[col]):
            return {"erro": f"Coluna '{col}' não é numérica (tipo: {df[col].dtype})."}

    if metodo not in {"pearson", "spearman"}:
        return {"erro": f"Método '{metodo}' inválido. Use 'pearson' ou 'spearman'."}

    valor = df[coluna_a].corr(df[coluna_b], method=metodo)

    # Interpretação simples baseada em magnitude
    abs_val = abs(valor)
    if abs_val < 0.1:
        interpretacao = "desprezível"
    elif abs_val < 0.3:
        interpretacao = "fraca"
    elif abs_val < 0.7:
        interpretacao = "moderada"
    else:
        interpretacao = "forte"

    sinal = "positiva" if valor > 0 else "negativa"

    return {
        "coluna_a": coluna_a,
        "coluna_b": coluna_b,
        "metodo": metodo,
        "correlacao": round(float(valor), 4),
        "interpretacao": f"{interpretacao} e {sinal}",
    }


# ============================================================
# detectar_outliers
# ============================================================

@tool(
    description=(
        "Detecta outliers em uma coluna numérica. "
        "Métodos disponíveis: 'iqr' (intervalo interquartil) ou 'zscore'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna": {"type": "string"},
            "metodo": {
                "type": "string",
                "enum": ["iqr", "zscore"],
                "description": "Método de detecção (default: iqr).",
            },
        },
        "required": ["coluna"],
    },
)
def detectar_outliers(coluna: str, metodo: str = "iqr") -> dict:
    """
    Detecta outliers em uma coluna.

    IQR: outlier se valor < Q1 - 1.5*IQR ou valor > Q3 + 1.5*IQR.
    Z-score: outlier se |z| > 3.
    """
    df = state.require_loaded()

    if coluna not in df.columns:
        return {"erro": f"Coluna '{coluna}' não existe."}
    if not pd.api.types.is_numeric_dtype(df[coluna]):
        return {"erro": f"Coluna '{coluna}' não é numérica."}

    serie = df[coluna].dropna()

    if metodo == "iqr":
        q1 = serie.quantile(0.25)
        q3 = serie.quantile(0.75)
        iqr = q3 - q1
        limite_inf = q1 - 1.5 * iqr
        limite_sup = q3 + 1.5 * iqr
        outliers = serie[(serie < limite_inf) | (serie > limite_sup)]

        return {
            "coluna": coluna,
            "metodo": "iqr",
            "limite_inferior": round(float(limite_inf), 3),
            "limite_superior": round(float(limite_sup), 3),
            "total_outliers": int(len(outliers)),
            "porcentagem": round(len(outliers) / len(serie) * 100, 2),
            "exemplos": [round(float(v), 3) for v in outliers.head(5).tolist()],
        }

    elif metodo == "zscore":
        # TODO (alunos): implementar a detecção por z-score.
        #
        # Passos:
        #   1. Calcular média e desvio-padrão da série.
        #   2. Calcular o z-score para cada valor: z = (x - media) / std
        #   3. Considerar outliers aqueles com |z| > 3.
        #   4. Retornar dict no mesmo formato do método 'iqr' acima
        #      (adapte os campos para refletir z-score: limite_z, etc).
        return {"erro": "Método z-score ainda não implementado. Veja o TODO no código."}

    return {"erro": f"Método '{metodo}' não reconhecido."}
