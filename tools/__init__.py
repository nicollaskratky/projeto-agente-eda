"""
Pacote de ferramentas (tools) do agente.

Importante: importar TODOS os módulos aqui faz com que os decoradores
@tool sejam executados, registrando as funções no TOOL_REGISTRY.
"""

from .base import (
    state,
    tool,
    TOOL_REGISTRY,
    ToolSpec,
    get_tool_by_name,
    all_tools_for_llm,
)

# Imports que disparam o registro das tools nos módulos:
from . import inspect_tools   # listar_colunas, descrever_dados, contar_valores
from . import filter_tools    # filtrar, agrupar_e_agregar, tempo_total_piloto, analisar_tempo
from . import stats_tools     # correlacao, detectar_outliers
from . import plot_tools      # gerar_grafico

