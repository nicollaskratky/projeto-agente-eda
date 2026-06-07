"""
Cliente da API do LLM.

Encapsula a chamada à API para que o resto do código não precise
saber qual provedor está sendo usado. Se quiserem trocar de provedor,
mexem APENAS aqui.

Este arquivo já vem implementado para a API da Anthropic.
Para usar outros provedores, criem variantes (LLMClientOpenAI etc).
"""

from __future__ import annotations
from dataclasses import dataclass
import time

from anthropic import Anthropic

from config import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    MAX_TOKENS_PER_RESPONSE,
)


# ============================================================
# Estruturas de retorno
# ============================================================

@dataclass
class LLMResponse:
    """Resposta tipada do LLM, independente do provedor."""
    text: str                          # Texto livre gerado (pode ser vazio)
    tool_calls: list[dict]             # Lista de chamadas de tool (pode ser vazia)
    raw_response: object               # Resposta crua do SDK (para debug)
    input_tokens: int                  # Tokens enviados
    output_tokens: int                 # Tokens gerados
    stop_reason: str                   # 'end_turn', 'tool_use', etc.
    latency_seconds: float             # Tempo da chamada


# ============================================================
# Cliente Anthropic
# ============================================================

class LLMClient:
    """Cliente que se comunica com a API da Anthropic (Claude)."""

    def __init__(self, model: str = LLM_MODEL, api_key: str = ANTHROPIC_API_KEY):
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY não definida. Configure no arquivo .env."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def chat(
        self,
        messages: list[dict],
        tools: list[dict],
        system: str = "",
    ) -> LLMResponse:
        """
        Envia uma rodada de mensagens ao LLM.

        Args:
            messages: histórico no formato Anthropic.
            tools: lista de tools disponíveis (formato Anthropic).
            system: prompt de sistema (instruções gerais do agente).

        Returns:
            LLMResponse com texto, chamadas de tool e métricas.
        """
        kwargs = {
            "model": self.model,
            "max_tokens": MAX_TOKENS_PER_RESPONSE,
            "messages": messages,
            "tools": tools,
        }
        if system:
            kwargs["system"] = system

        inicio = time.perf_counter()
        resp = self.client.messages.create(**kwargs)
        latencia = time.perf_counter() - inicio

        # Extrai blocos de texto e de tool_use da resposta
        texto = ""
        tool_calls = []
        for bloco in resp.content:
            if bloco.type == "text":
                texto += bloco.text
            elif bloco.type == "tool_use":
                tool_calls.append({
                    "id": bloco.id,
                    "name": bloco.name,
                    "input": bloco.input,
                })

        return LLMResponse(
            text=texto,
            tool_calls=tool_calls,
            raw_response=resp,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            stop_reason=resp.stop_reason,
            latency_seconds=latencia,
        )
