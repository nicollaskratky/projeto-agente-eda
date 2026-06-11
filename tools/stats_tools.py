import numpy as np
import pandas as pd
from tools.base import tool, state


@tool(
    description=(
        "Calcula a correlação entre duas colunas numéricas. "
        "Método Pearson para dados lineares ou Spearman para dados não-lineares."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna_a": {
                "type": "string",
                "description": "Nome da primeira coluna numérica.",
            },
            "coluna_b": {
                "type": "string",
                "description": "Nome da segunda coluna numérica.",
            },
            "metodo": {
                "type": "string",
                "description": "Método de correlação: 'pearson' (padrão) ou 'spearman'.",
            },
        },
        "required": ["coluna_a", "coluna_b"],
    },
)
def correlacao(coluna_a: str, coluna_b: str, metodo: str = "pearson") -> dict:
    df = state.require_loaded()

    if coluna_a not in df.columns:
        return {"erro": f"Coluna '{coluna_a}' não existe."}
    if coluna_b not in df.columns:
        return {"erro": f"Coluna '{coluna_b}' não existe."}

    metodos_validos = ["pearson", "spearman"]
    if metodo not in metodos_validos:
        return {"erro": f"Método '{metodo}' inválido. Use: {metodos_validos}"}

    try:
        valor = df[coluna_a].corr(df[coluna_b], method=metodo)
    except Exception as e:
        return {"erro": str(e)}

    if valor > 0.7:
        interpretacao = "correlação positiva forte"
    elif valor > 0.4:
        interpretacao = "correlação positiva moderada"
    elif valor > 0:
        interpretacao = "correlação positiva fraca"
    elif valor > -0.4:
        interpretacao = "correlação negativa fraca"
    elif valor > -0.7:
        interpretacao = "correlação negativa moderada"
    else:
        interpretacao = "correlação negativa forte"

    return {
        "coluna_a": coluna_a,
        "coluna_b": coluna_b,
        "metodo": metodo,
        "correlacao": round(float(valor), 4),
        "interpretacao": interpretacao,
    }


@tool(
    description=(
        "Detecta outliers em uma coluna numérica usando IQR ou z-score. "
        "IQR: valores abaixo de Q1-1.5*IQR ou acima de Q3+1.5*IQR. "
        "Z-score: valores com |z| > 3."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna": {
                "type": "string",
                "description": "Nome da coluna numérica para analisar.",
            },
            "metodo": {
                "type": "string",
                "description": "Método de detecção: 'iqr' (padrão) ou 'zscore'.",
            },
        },
        "required": ["coluna"],
    },
)
def detectar_outliers(coluna: str, metodo: str = "iqr") -> dict:
    df = state.require_loaded()

    if coluna not in df.columns:
        return {"erro": f"Coluna '{coluna}' não existe."}

    metodos_validos = ["iqr", "zscore"]
    if metodo not in metodos_validos:
        return {"erro": f"Método '{metodo}' inválido. Use: {metodos_validos}"}

    if not pd.api.types.is_numeric_dtype(df[coluna]):
        return {"erro": f"Coluna '{coluna}' não é numérica. Outliers só podem ser detectados em colunas numéricas."}

    serie = df[coluna].dropna()

    if metodo == "iqr":
        q1 = serie.quantile(0.25)
        q3 = serie.quantile(0.75)
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr
        outliers = serie[(serie < limite_inferior) | (serie > limite_superior)]

        return {
            "coluna": coluna,
            "metodo": "iqr",
            "q1": round(float(q1), 3),
            "q3": round(float(q3), 3),
            "iqr": round(float(iqr), 3),
            "limite_inferior": round(float(limite_inferior), 3),
            "limite_superior": round(float(limite_superior), 3),
            "total_outliers": int(len(outliers)),
            "percentual": round(float(len(outliers) / len(serie) * 100), 2),
            "exemplos": [round(float(v), 3) for v in outliers.head(5).tolist()],
        }

    else:  # zscore
        media = serie.mean()
        desvio = serie.std()
        zscores = (serie - media) / desvio
        outliers = serie[abs(zscores) > 3]

        return {
            "coluna": coluna,
            "metodo": "zscore",
            "media": round(float(media), 3),
            "desvio_padrao": round(float(desvio), 3),
            "limite": 3,
            "total_outliers": int(len(outliers)),
            "percentual": round(float(len(outliers) / len(serie) * 100), 2),
            "exemplos": [round(float(v), 3) for v in outliers.head(5).tolist()],
        }
