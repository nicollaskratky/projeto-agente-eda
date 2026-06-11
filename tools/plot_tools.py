import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from config import OUTPUTS_DIR
from tools.base import tool, state


@tool(
    description=(
        "Gera um gráfico e salva como imagem PNG na pasta outputs/. "
        "Tipos disponíveis: 'histograma', 'boxplot', 'scatter', 'barplot'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "tipo": {
                "type": "string",
                "description": "Tipo do gráfico: 'histograma', 'boxplot', 'scatter', 'barplot'.",
            },
            "colunas": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Lista de colunas a usar. "
                    "histograma/boxplot: 1 coluna. "
                    "scatter: 2 colunas [x, y]. "
                    "barplot: 2 colunas [categoria, valor]."
                ),
            },
            "titulo": {
                "type": "string",
                "description": "Título do gráfico (opcional).",
            },
            "top_n": {
                "type": "integer",
                "description": "Para barplot: quantas categorias exibir. Padrão: 10.",
            },
        },
        "required": ["tipo", "colunas"],
    },
)
def gerar_grafico(tipo: str, colunas: list, titulo: str = "", top_n: int = 10) -> dict:
    df = state.require_loaded()

    tipos_validos = ["histograma", "boxplot", "scatter", "barplot"]
    if tipo not in tipos_validos:
        return {"erro": f"Tipo '{tipo}' inválido. Use: {tipos_validos}"}

    for col in colunas:
        if col not in df.columns:
            return {"erro": f"Coluna '{col}' não existe."}

    OUTPUTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{tipo}_{'-'.join(colunas)}_{timestamp}.png"
    caminho = OUTPUTS_DIR / nome_arquivo

    fig, ax = plt.subplots(figsize=(10, 6))

    try:
        if tipo == "histograma":
            ax.hist(df[colunas[0]].dropna(), bins=30, color="steelblue", edgecolor="white")
            ax.set_xlabel(colunas[0])
            ax.set_ylabel("Frequência")

        elif tipo == "boxplot":
            ax.boxplot(df[colunas[0]].dropna(), patch_artist=True,
                       boxprops=dict(facecolor="steelblue", color="navy"))
            ax.set_ylabel(colunas[0])

        elif tipo == "scatter":
            if len(colunas) < 2:
                return {"erro": "scatter requer 2 colunas: [x, y]."}
            ax.scatter(df[colunas[0]], df[colunas[1]], alpha=0.5, color="steelblue")
            ax.set_xlabel(colunas[0])
            ax.set_ylabel(colunas[1])

        elif tipo == "barplot":
            if len(colunas) < 2:
                return {"erro": "barplot requer 2 colunas: [categoria, valor]."}
            dados = (
                df.groupby(colunas[0])[colunas[1]]
                .sum()
                .sort_values(ascending=False)
                .head(top_n)
            )
            ax.barh(dados.index[::-1], dados.values[::-1], color="steelblue")
            ax.set_xlabel(colunas[1])
            ax.set_ylabel(colunas[0])

        ax.set_title(titulo or f"{tipo.capitalize()} — {', '.join(colunas)}")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(caminho, dpi=100)
        plt.close()

    except Exception as e:
        plt.close()
        return {"erro": str(e)}

    return {
        "tipo": tipo,
        "colunas": colunas,
        "arquivo": nome_arquivo,
        "caminho": str(caminho),
    }
