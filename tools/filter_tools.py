"""
Ferramentas de filtragem e agregação.

Estas tools transformam o dataset (recortes, grupos) e produzem
estatísticas resumidas. Geralmente vêm DEPOIS de uma chamada a
listar_colunas, quando o agente já sabe o que filtrar.
"""

import re
import pandas as pd
from .base import tool, state


# ============================================================
# filtrar
# ============================================================

@tool(
    description=(
        "Filtra o dataset com uma expressão de consulta (sintaxe pandas .query) "
        "e retorna estatísticas do subconjunto resultante.\n\n"
        "Exemplos de expressão válida:\n"
        "  - 'idade > 30'\n"
        "  - \"sexo == 'F' and renda > 5000\"\n"
        "  - 'pais in [\"Brasil\", \"Argentina\"]'\n\n"
        "Atenção: nomes de colunas com espaço devem usar crase no pandas query."
    ),
    parameters={
        "type": "object",
        "properties": {
            "condicao": {
                "type": "string",
                "description": "Expressão de filtro no formato pandas .query()",
            },
        },
        "required": ["condicao"],
    },
)
def filtrar(condicao: str) -> dict:
    """
    Filtra e retorna estatísticas do subconjunto.

    Note: a expressão é avaliada por df.query() — segura porque o pandas
    não permite execução de código arbitrário neste contexto.
    """
    df = state.require_loaded()

    try:
        filtrado = df.query(condicao)
    except Exception as e:
        return {
            "erro": f"Expressão inválida: {e}",
            "dica": "Verifique os nomes das colunas e a sintaxe pandas query.",
        }

    if len(filtrado) == 0:
        return {
            "condicao": condicao,
            "linhas_resultantes": 0,
            "aviso": "Nenhuma linha satisfaz a condição.",
        }

    # Estatísticas numéricas do recorte
    num_cols = filtrado.select_dtypes(include="number").columns.tolist()
    estatisticas = {}
    for col in num_cols:
        estatisticas[col] = {
            "media": round(float(filtrado[col].mean()), 3),
            "mediana": round(float(filtrado[col].median()), 3),
            "min": round(float(filtrado[col].min()), 3),
            "max": round(float(filtrado[col].max()), 3),
        }

    return {
        "condicao": condicao,
        "linhas_resultantes": len(filtrado),
        "porcentagem_do_total": round(len(filtrado) / len(df) * 100, 2),
        "estatisticas": estatisticas,
    }


# ============================================================
# agrupar_e_agregar
# ============================================================

# Funções de agregação aceitas
FUNCOES_VALIDAS = {"mean", "median", "sum", "min", "max", "count", "std"}


@tool(
    description=(
        "Agrupa o dataset por uma coluna e aplica uma função de agregação "
        "sobre outra coluna. Equivalente a df.groupby(grupo)[coluna].agg(funcao).\n\n"
        "Use o parâmetro opcional `filtro` (sintaxe pandas .query) para restringir "
        "o dataset ANTES de agrupar — evitando uma chamada separada a `filtrar`.\n\n"
        "Exemplos:\n"
        "  - Vitórias por piloto (Position==1): grupo='Driver', coluna='Position', "
        "funcao='count', filtro='Position == 1'\n"
        "  - Pontos por equipe em 2023: grupo='Team', coluna='Points', "
        "funcao='sum', filtro='season == 2023'\n"
        "  - Poles por equipe: grupo='Team', coluna='Position', funcao='count', "
        "filtro='`Starting Grid` == 1'\n\n"
        "Funções válidas: mean, median, sum, min, max, count, std."
    ),
    parameters={
        "type": "object",
        "properties": {
            "grupo": {
                "type": "string",
                "description": "Coluna pela qual agrupar (geralmente categórica).",
            },
            "coluna": {
                "type": "string",
                "description": "Coluna sobre a qual aplicar a agregação (geralmente numérica).",
            },
            "funcao": {
                "type": "string",
                "enum": list(FUNCOES_VALIDAS),
                "description": "Função de agregação.",
            },
            "filtro": {
                "type": "string",
                "description": (
                    "Expressão pandas .query() opcional para filtrar o dataset "
                    "antes do agrupamento. Ex.: 'season == 2023' ou 'Position == 1'."
                ),
            },
        },
        "required": ["grupo", "coluna", "funcao"],
    },
)
def agrupar_e_agregar(grupo: str, coluna: str, funcao: str, filtro: str = "") -> dict:
    """Groupby + agg com filtro opcional pré-agrupamento."""
    df = state.require_loaded()

    # Aplica filtro se fornecido
    if filtro:
        try:
            df = df.query(filtro)
        except Exception as e:
            return {"erro": f"Filtro inválido: {e}"}
        if len(df) == 0:
            return {"erro": f"Nenhuma linha após aplicar filtro: {filtro!r}"}

    # Validações
    if grupo not in df.columns:
        return {"erro": f"Coluna de grupo '{grupo}' não existe."}
    if coluna not in df.columns:
        return {"erro": f"Coluna '{coluna}' não existe."}
    if funcao not in FUNCOES_VALIDAS:
        return {"erro": f"Função '{funcao}' inválida. Use uma de {FUNCOES_VALIDAS}."}

    # 'count' funciona em qualquer tipo; as demais exigem numérico
    if funcao != "count" and not pd.api.types.is_numeric_dtype(df[coluna]):
        return {
            "erro": (
                f"Função '{funcao}' requer coluna numérica, "
                f"mas '{coluna}' é {df[coluna].dtype}."
            )
        }

    resultado = df.groupby(grupo)[coluna].agg(funcao)

    return {
        "grupo": grupo,
        "coluna": coluna,
        "funcao": funcao,
        "filtro_aplicado": filtro or None,
        "resultados": {
            str(k): round(float(v), 3) if pd.notna(v) else None
            for k, v in resultado.items()
        },
    }


# ============================================================
# Ferramentas de análise de tempo
# ============================================================

def _parse_tempo_segundos(valor: str) -> float | None:
    """
    Converte uma string de tempo para segundos (float).

    Formatos suportados:
      H:MM:SS.mmm   → ex: "1:37:33.584"  (Race Time do vencedor)
      M:SS.mmm      → ex: "1:34.570"     (Fastest Lap Time)
      +S.mmm        → ex: "+5.598"       (diferença para o líder)
      +MM:SS.mmm    → ex: "+1:23.456"    (diferença > 1 min)
    Retorna None para valores inválidos ("0", vazio, etc.).
    """
    if not isinstance(valor, str):
        return None
    valor = valor.strip()
    if not valor or valor == "0":
        return None

    # +S.mmm ou +MM:SS.mmm (diferença para o líder)
    if valor.startswith("+"):
        inner = valor[1:]
        parts = inner.split(":")
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])

    # H:MM:SS.mmm ou M:SS.mmm
    parts = valor.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])

    return None


def _segundos_para_hms(segundos: float) -> str:
    """Formata segundos como H:MM:SS.mmm ou MM:SS.mmm."""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = segundos % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:06.3f}"
    return f"{m}:{s:06.3f}"


@tool(
    description=(
        "Converte uma coluna de tempo textual (Race Time ou Fastest Lap Time) para segundos "
        "e calcula estatísticas ou soma sobre o resultado. "
        "Para Race Time: só processa tempos absolutos (vencedores, formato H:MM:SS.mmm); "
        "tempos relativos (+S.mmm) também são suportados. "
        "Para Fastest Lap Time: formato M:SS.mmm. "
        "Operações disponíveis: sum, mean, min, max, count. "
        "Use condicao para filtrar antes de calcular (ex: 'Driver == \"Lewis Hamilton\"'). "
        "Exemplos de uso: tempo total de corrida de um piloto, média de volta rápida por equipe."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna": {
                "type": "string",
                "description": "Nome da coluna de tempo: 'Race Time' ou 'Fastest Lap Time'.",
            },
            "operacao": {
                "type": "string",
                "description": "Operação a realizar: sum, mean, min, max, count.",
            },
            "condicao": {
                "type": "string",
                "description": "Filtro opcional no formato pandas query. Ex: 'season == 2023 and Position == 1'.",
            },
        },
        "required": ["coluna", "operacao"],
    },
)
def analisar_tempo(coluna: str, operacao: str, condicao: str = "") -> dict:
    """Analisa tempos convertendo para segundos e aplicando operações."""
    df = state.require_loaded()

    colunas_validas = ["Race Time", "Fastest Lap Time"]
    if coluna not in colunas_validas:
        return {"erro": f"Coluna '{coluna}' não suportada. Use: {colunas_validas}"}

    operacoes_validas = ["sum", "mean", "min", "max", "count"]
    if operacao not in operacoes_validas:
        return {"erro": f"Operação '{operacao}' inválida. Use: {operacoes_validas}"}

    if condicao:
        try:
            df = df.query(condicao)
        except Exception as e:
            return {"erro": f"Condição inválida: {e}"}
        if df.empty:
            return {"erro": f"Nenhum registro para a condição: '{condicao}'"}

    serie_seg = df[coluna].apply(_parse_tempo_segundos).dropna()
    # Ignora tempos absurdamente curtos (corridas interrompidas com tempo < 60s)
    if coluna == "Race Time":
        serie_seg = serie_seg[serie_seg >= 60]

    if serie_seg.empty:
        return {"erro": f"Nenhum valor de tempo válido encontrado em '{coluna}' com os filtros aplicados."}

    if operacao == "sum":
        val = serie_seg.sum()
        return {
            "coluna": coluna, "operacao": "sum", "condicao": condicao,
            "total_registros_validos": len(serie_seg),
            "resultado_segundos": round(val, 3),
            "resultado_formatado": _segundos_para_hms(val),
        }
    elif operacao == "mean":
        val = serie_seg.mean()
        return {
            "coluna": coluna, "operacao": "mean", "condicao": condicao,
            "total_registros_validos": len(serie_seg),
            "resultado_segundos": round(val, 3),
            "resultado_formatado": _segundos_para_hms(val),
        }
    elif operacao == "min":
        val = serie_seg.min()
        idx = serie_seg.idxmin()
        return {
            "coluna": coluna, "operacao": "min", "condicao": condicao,
            "total_registros_validos": len(serie_seg),
            "resultado_segundos": round(val, 3),
            "resultado_formatado": _segundos_para_hms(val),
            "piloto": df.loc[idx, "Driver"] if idx in df.index else None,
            "circuito": df.loc[idx, "Track"] if idx in df.index else None,
            "temporada": int(df.loc[idx, "season"]) if idx in df.index else None,
        }
    elif operacao == "max":
        val = serie_seg.max()
        idx = serie_seg.idxmax()
        return {
            "coluna": coluna, "operacao": "max", "condicao": condicao,
            "total_registros_validos": len(serie_seg),
            "resultado_segundos": round(val, 3),
            "resultado_formatado": _segundos_para_hms(val),
            "piloto": df.loc[idx, "Driver"] if idx in df.index else None,
            "circuito": df.loc[idx, "Track"] if idx in df.index else None,
            "temporada": int(df.loc[idx, "season"]) if idx in df.index else None,
        }
    elif operacao == "count":
        return {
            "coluna": coluna, "operacao": "count", "condicao": condicao,
            "total_registros_validos": len(serie_seg),
        }


@tool(
    description=(
        "Retorna o tempo total de corrida de um piloto em uma corrida específica. "
        "Se o piloto venceu, retorna o tempo absoluto direto. "
        "Se terminou com atraso em segundos (+S.mmm), soma ao tempo do vencedor e retorna o total. "
        "Se terminou X voltas atrás do líder (+X lap/laps), informa quantas voltas de atraso. "
        "Use para responder: 'Qual foi o tempo total de [piloto] em [circuito] [ano]?'"
    ),
    parameters={
        "type": "object",
        "properties": {
            "piloto": {
                "type": "string",
                "description": "Nome exato do piloto. Ex: 'Lewis Hamilton', 'Max Verstappen'.",
            },
            "circuito": {
                "type": "string",
                "description": "Nome do circuito. Ex: 'Bahrain', 'Monaco', 'Silverstone'.",
            },
            "temporada": {
                "type": "integer",
                "description": "Ano da temporada. Ex: 2023.",
            },
        },
        "required": ["piloto", "circuito", "temporada"],
    },
)
def tempo_total_piloto(piloto: str, circuito: str, temporada: int) -> dict:
    """Retorna tempo total de um piloto em uma corrida específica."""
    df = state.require_loaded()

    corrida = df[(df["Track"] == circuito) & (df["season"] == temporada)]
    if corrida.empty:
        return {"erro": f"Corrida não encontrada: {circuito} {temporada}. Verifique o nome do circuito e a temporada."}

    linha_piloto = corrida[corrida["Driver"] == piloto]
    if linha_piloto.empty:
        pilotos_disponiveis = corrida["Driver"].tolist()
        return {"erro": f"Piloto '{piloto}' não encontrado em {circuito} {temporada}.", "pilotos_na_corrida": pilotos_disponiveis}

    linha_piloto = linha_piloto.iloc[0]
    race_time_raw = str(linha_piloto["Race Time"]).strip()
    posicao = int(linha_piloto["Position"])
    status = int(linha_piloto["Status"])

    # Caso: piloto não terminou (DNF/DNS/DQ)
    status_map = {1: "Finished", 2: "NC", 3: "DNF", 4: "DNS", 5: "DQ"}
    if status in (3, 4, 5):
        return {
            "piloto": piloto, "circuito": circuito, "temporada": temporada,
            "posicao": posicao, "status": status_map.get(status, "Desconhecido"),
            "tempo_total": None,
            "observacao": f"O piloto não concluiu a corrida (Status: {status_map.get(status)}).",
        }

    # Caso: "+X lap(s)" — terminou voltas atrás
    lap_match = re.match(r'^\+(\d+)\s+laps?$', race_time_raw, re.IGNORECASE)
    if lap_match:
        n_laps = int(lap_match.group(1))
        return {
            "piloto": piloto, "circuito": circuito, "temporada": temporada,
            "posicao": posicao, "status": "Finished",
            "tempo_total": None,
            "observacao": f"O piloto terminou {n_laps} {'volta' if n_laps == 1 else 'voltas'} atrás do líder. Tempo total exato não disponível.",
        }

    # Tempo do vencedor da corrida
    vencedor = corrida[corrida["Position"] == 1].iloc[0] if not corrida[corrida["Position"] == 1].empty else None

    # Caso: tempo absoluto (piloto venceu ou temos o tempo direto)
    seg_piloto = _parse_tempo_segundos(race_time_raw)
    if seg_piloto is not None and not race_time_raw.startswith("+"):
        return {
            "piloto": piloto, "circuito": circuito, "temporada": temporada,
            "posicao": posicao, "status": "Finished",
            "tempo_total_segundos": round(seg_piloto, 3),
            "tempo_total_formatado": _segundos_para_hms(seg_piloto),
            "observacao": "Tempo absoluto da corrida.",
        }

    # Caso: tempo relativo (+S.mmm ou +MM:SS.mmm) — soma ao tempo do vencedor
    if race_time_raw.startswith("+") and vencedor is not None:
        seg_relativo = _parse_tempo_segundos(race_time_raw)
        seg_vencedor = _parse_tempo_segundos(str(vencedor["Race Time"]).strip())

        if seg_relativo is not None and seg_vencedor is not None:
            seg_total = seg_vencedor + seg_relativo
            return {
                "piloto": piloto, "circuito": circuito, "temporada": temporada,
                "posicao": posicao, "status": "Finished",
                "tempo_total_segundos": round(seg_total, 3),
                "tempo_total_formatado": _segundos_para_hms(seg_total),
                "atraso_para_o_lider": race_time_raw,
                "tempo_vencedor": str(vencedor["Race Time"]),
                "vencedor": vencedor["Driver"],
                "observacao": "Tempo calculado somando o atraso ao tempo absoluto do vencedor.",
            }

    return {
        "piloto": piloto, "circuito": circuito, "temporada": temporada,
        "posicao": posicao,
        "race_time_raw": race_time_raw,
        "observacao": "Não foi possível calcular o tempo total com os dados disponíveis.",
    }