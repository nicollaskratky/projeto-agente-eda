import pandas as pd
from tools.base import tool, state


@tool(
    description="Retorna os nomes e tipos de cada coluna do dataset.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def listar_colunas() -> dict:
    df = state.require_loaded()
    return {
        "colunas": [
            {"nome": col, "tipo": str(df[col].dtype)}
            for col in df.columns
        ],
        "total": len(df.columns),
    }


@tool(
    description=(
        "Retorna estatísticas descritivas do dataset. "
        "Para colunas numéricas: média, desvio padrão, min, max, quartis. "
        "Para colunas categóricas: contagem, valores únicos, valor mais frequente."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def descrever_dados() -> dict:
    df = state.require_loaded()

    numericas = {}
    for col in df.select_dtypes(include="number").columns:
        s = df[col]
        numericas[col] = {
            "media": round(float(s.mean()), 3),
            "desvio_padrao": round(float(s.std()), 3),
            "min": round(float(s.min()), 3),
            "max": round(float(s.max()), 3),
            "q25": round(float(s.quantile(0.25)), 3),
            "q50": round(float(s.quantile(0.50)), 3),
            "q75": round(float(s.quantile(0.75)), 3),
            "nulos": int(s.isna().sum()),
        }

    categoricas = {}
    for col in df.select_dtypes(include="object").columns:
        s = df[col]
        categoricas[col] = {
            "total": int(s.count()),
            "unicos": int(s.nunique()),
            "mais_frequente": str(s.mode()[0]) if not s.mode().empty else None,
            "nulos": int(s.isna().sum()),
        }

    return {
        "linhas": len(df),
        "colunas": len(df.columns),
        "numericas": numericas,
        "categoricas": categoricas,
    }


@tool(
    description="Retorna a distribuição de valores de uma coluna específica.",
    parameters={
        "type": "object",
        "properties": {
            "coluna": {
                "type": "string",
                "description": "Nome da coluna a analisar.",
            },
            "top_n": {
                "type": "integer",
                "description": "Quantos valores mais frequentes retornar. Padrão: 10.",
            },
        },
        "required": ["coluna"],
    },
)
def contar_valores(coluna: str, top_n: int = 10) -> dict:
    df = state.require_loaded()

    if coluna not in df.columns:
        return {"erro": f"Coluna '{coluna}' não existe. Use listar_colunas() para ver as disponíveis."}

    contagem = df[coluna].value_counts().head(top_n)
    return {
        "coluna": coluna,
        "top_n": top_n,
        "total_unicos": int(df[coluna].nunique()),
        "distribuicao": {str(k): int(v) for k, v in contagem.items()},
    }
