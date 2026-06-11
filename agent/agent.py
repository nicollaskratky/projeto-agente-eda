"""
Agente principal.

Implementa o loop de raciocínio:

    pergunta_usuario
        |
        v
    [LLM raciocina sobre o que fazer]
        |
        v
    LLM gerou tool_call? --- sim ---> [executa tool] --- adiciona resultado ---+
        |                                                                      |
        | não (stop_reason == 'end_turn')                                       |
        v                                                                      |
    [resposta final em texto]                                                  |
        ^                                                                      |
        |                                                                      |
        +----------------------------------------------------------------------+

Limitamos a MAX_AGENT_ITERATIONS para evitar loops infinitos.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import json

from .llm_client import LLMClient, LLMResponse
from tools import all_tools_for_llm, get_tool_by_name, state
from config import MAX_AGENT_ITERATIONS


# ============================================================
# Estruturas para registrar a trajetória do agente
# ============================================================

@dataclass
class Step:
    """Um passo da trajetória: ou um pensamento do LLM, ou uma chamada de tool."""
    tipo: str                              # 'llm_text' | 'tool_call' | 'tool_result'
    conteudo: dict | str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentResult:
    """Resultado completo de uma pergunta processada pelo agente."""
    pergunta: str
    resposta_final: str
    sucesso: bool                          # Terminou normalmente?
    trajetoria: list[Step]                 # Cada passo intermediário
    total_iteracoes: int
    total_tool_calls: int
    input_tokens: int
    output_tokens: int
    latencia_total: float

    def to_dict(self) -> dict:
        return {
            "pergunta": self.pergunta,
            "resposta_final": self.resposta_final,
            "sucesso": self.sucesso,
            "total_iteracoes": self.total_iteracoes,
            "total_tool_calls": self.total_tool_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latencia_total": round(self.latencia_total, 3),
            "trajetoria": [
                {"tipo": s.tipo, "conteudo": s.conteudo, "timestamp": s.timestamp}
                for s in self.trajetoria
            ],
        }


# ============================================================
# Prompt de sistema
# ============================================================

SYSTEM_PROMPT = """\
Você é um assistente de análise exploratória de dados.

Sua tarefa é responder perguntas em português sobre um arquivo CSV carregado
em memória. Você NÃO tem acesso direto aos dados — use as ferramentas (tools)
disponíveis para inspecionar e operar sobre o dataset.

## Escolha da ferramenta certa (IMPORTANTE)

Use `agrupar_e_agregar` sempre que a pergunta envolver:
- "quem ganhou MAIS / menos" → agrupar_e_agregar(grupo="Driver", coluna="Position", funcao="count") após filtrar
- "qual equipe somou mais pontos" → agrupar_e_agregar(grupo="Team", coluna="Points", funcao="sum")
- "quantas vitórias cada piloto teve" → agrupar_e_agregar(grupo="Driver", coluna="Points", funcao="count")
- "top N pilotos/equipes" → agrupar_e_agregar + ordenar pelo resultado
- qualquer ranking, contagem por categoria ou soma por grupo

NÃO use `filtrar` repetidamente para testar cada piloto/equipe um a um.
Isso é ineficiente e esgota as iterações disponíveis.
Use `filtrar` apenas para recortar o dataset ANTES de agrupar (ex.: filtrar
por temporada) ou quando quiser estatísticas de um subconjunto específico já
conhecido.

Fluxo correto para perguntas de ranking:
  1. (Opcional) filtrar para restringir ao período/temporada desejado — mas
     prefira passar a condição diretamente via `filtrar` uma única vez.
  2. agrupar_e_agregar para obter o total/contagem por categoria.
  3. Ordenar mentalmente o resultado e identificar o maior/menor.
  4. Responder diretamente — não precisa confirmar com filtros adicionais.

Para contar vitórias (Position == 1), o caminho correto é UMA única chamada:
  agrupar_e_agregar(grupo="Driver", coluna="Position", funcao="count", filtro="Position == 1")

Para poles por equipe em 2023:
  agrupar_e_agregar(grupo="Team", coluna="Position", funcao="count", filtro="season == 2023 and `Starting Grid` == 1")

## Regras gerais

1. Chame `listar_colunas` na primeira pergunta se ainda não conhecer o schema.
2. Use os NOMES EXATOS das colunas retornados por `listar_colunas`.
3. Se a pergunta for ambígua ou impossível de responder com os dados
   disponíveis (ex.: previsões futuras, história além do dataset), diga isso
   explicitamente e explique o que o dataset cobre (temporadas 2019–2024).
4. Use o menor número de tool calls necessário. Não confirme com filtros
   extras o que já foi provado pelo agrupamento.
5. Responda em português claro e conciso. Números com formato legível
   (ex.: 1.234 em vez de 1234).
6. Use apenas informações obtidas pelas tools. Não use conhecimento externo.
7. Se uma tool retornar erro, corrija a chamada. Não repita o mesmo erro.
"""


# ============================================================
# Classe Agent
# ============================================================

class Agent:
    """Orquestrador do loop de raciocínio do agente."""

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.tools_para_llm = all_tools_for_llm()

    def _executar_tool(self, tool_call: dict) -> dict:
        """
        Executa uma tool e retorna seu resultado.

        Captura exceções para o agente nunca travar - se a tool falhar,
        o erro é devolvido ao LLM, que pode tentar outra abordagem.
        """
        nome = tool_call["name"]
        argumentos = tool_call["input"]
        spec = get_tool_by_name(nome)

        if spec is None:
            return {"erro": f"Tool '{nome}' não encontrada no registro."}

        try:
            return spec.function(**argumentos)
        except TypeError as e:
            # Argumentos errados
            return {"erro": f"Argumentos inválidos para '{nome}': {e}"}
        except Exception as e:
            # Qualquer outro erro
            return {"erro": f"Erro ao executar '{nome}': {type(e).__name__}: {e}"}

    def perguntar(self, pergunta: str) -> AgentResult:
        """
        Processa uma pergunta e retorna o resultado completo, incluindo
        toda a trajetória para análise posterior.
        """
        # Verifica se tem dataset carregado antes de começar
        try:
            state.require_loaded()
        except RuntimeError as e:
            return AgentResult(
                pergunta=pergunta,
                resposta_final=str(e),
                sucesso=False,
                trajetoria=[],
                total_iteracoes=0,
                total_tool_calls=0,
                input_tokens=0,
                output_tokens=0,
                latencia_total=0.0,
            )

        # Histórico no formato Anthropic
        messages: list[dict] = [
            {"role": "user", "content": pergunta},
        ]

        trajetoria: list[Step] = []
        total_input = 0
        total_output = 0
        latencia_total = 0.0
        total_tool_calls = 0

        # ============ Loop principal ============
        for iteracao in range(MAX_AGENT_ITERATIONS):

            resposta: LLMResponse = self.llm.chat(
                messages=messages,
                tools=self.tools_para_llm,
                system=SYSTEM_PROMPT,
            )

            total_input += resposta.input_tokens
            total_output += resposta.output_tokens
            latencia_total += resposta.latency_seconds

            # Registra o que o LLM "pensou"/disse
            if resposta.text:
                trajetoria.append(Step(tipo="llm_text", conteudo=resposta.text))

            # Caso 1: LLM terminou (sem tool_use) — temos a resposta final
            if resposta.stop_reason == "end_turn" or not resposta.tool_calls:
                return AgentResult(
                    pergunta=pergunta,
                    resposta_final=resposta.text or "(sem resposta)",
                    sucesso=True,
                    trajetoria=trajetoria,
                    total_iteracoes=iteracao + 1,
                    total_tool_calls=total_tool_calls,
                    input_tokens=total_input,
                    output_tokens=total_output,
                    latencia_total=latencia_total,
                )

            # Caso 2: LLM quer chamar uma ou mais tools
            # Devemos adicionar ao histórico TODO o conteúdo retornado pelo LLM
            # (texto + tool_uses), e em seguida os tool_results.
            messages.append({
                "role": "assistant",
                "content": resposta.raw_response.content,
            })

            tool_results_para_llm = []
            for tc in resposta.tool_calls:
                total_tool_calls += 1
                trajetoria.append(Step(
                    tipo="tool_call",
                    conteudo={"nome": tc["name"], "argumentos": tc["input"]},
                ))

                resultado = self._executar_tool(tc)

                trajetoria.append(Step(tipo="tool_result", conteudo=resultado))

                tool_results_para_llm.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": json.dumps(resultado, ensure_ascii=False, default=str),
                })

            # Adiciona os resultados como mensagem do usuário (convenção Anthropic)
            messages.append({
                "role": "user",
                "content": tool_results_para_llm,
            })

        # Saiu do loop sem terminar — atingiu MAX_AGENT_ITERATIONS
        return AgentResult(
            pergunta=pergunta,
            resposta_final=(
                f"Limite de {MAX_AGENT_ITERATIONS} iterações atingido sem "
                "chegar a uma resposta final."
            ),
            sucesso=False,
            trajetoria=trajetoria,
            total_iteracoes=MAX_AGENT_ITERATIONS,
            total_tool_calls=total_tool_calls,
            input_tokens=total_input,
            output_tokens=total_output,
            latencia_total=latencia_total,
        )
