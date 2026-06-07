"""
Métricas de avaliação.

Comparar a resposta de um LLM em texto livre com um gabarito é um problema
não-trivial. Este módulo oferece uma abordagem PRAGMÁTICA por tipo de resposta:

  - numero_inteiro / numero_float: extrai o primeiro número da resposta e compara
                                   com tolerância numérica.
  - lista_strings:                 verifica se todos os itens esperados aparecem
                                   na resposta (case-insensitive, ignora ordem).
  - dict_numerico:                 verifica se todas as chaves esperadas aparecem
                                   na resposta com valores aproximadamente iguais.
  - categorica:                    verifica se a resposta contém alguma palavra-chave.

TODO (alunos):
  - O comparador atual é SIMPLES por design. Discutam no relatório suas
    limitações: e se a resposta certa estiver expressa de forma diferente?
    Considerem usar LLM-as-judge como melhoria.
"""

from __future__ import annotations
import re
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import NUMERIC_TOLERANCE, BENCHMARK_FILE, LOGS_DIR


# ============================================================
# Extração de valores a partir de texto livre
# ============================================================

def extrair_primeiro_numero(texto: str) -> float | None:
    """
    Tenta extrair o primeiro número que aparece no texto da resposta.

    Aceita formatos: 1234, 1.234, 1,234.56, 1.234,56, -3.14, 50%, etc.
    """
    if not texto:
        return None

    # Remove % e $ que podem grudar nos números
    texto_limpo = texto.replace("%", "").replace("$", "").replace("R$", "")

    # Procura por padrões numéricos: opcional sinal, dígitos, separador, dígitos
    # Casa "1.234,56", "1234.56", "1234", etc.
    padroes = [
        r"-?\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?",  # 1.234,56 ou 1,234.56
        r"-?\d+[.,]\d+",                          # 12,34 ou 12.34
        r"-?\d+",                                 # 1234
    ]

    for padrao in padroes:
        match = re.search(padrao, texto_limpo)
        if match:
            valor_str = match.group()
            # Normaliza: remove separador de milhar, converte vírgula em ponto
            if valor_str.count(",") > 0 and valor_str.count(".") > 0:
                # Tem ambos: o último é o decimal
                if valor_str.rfind(",") > valor_str.rfind("."):
                    valor_str = valor_str.replace(".", "").replace(",", ".")
                else:
                    valor_str = valor_str.replace(",", "")
            elif valor_str.count(",") == 1 and not valor_str[-1].isdigit() is False:
                # Vírgula sozinha: tratar como decimal
                valor_str = valor_str.replace(",", ".")
            try:
                return float(valor_str)
            except ValueError:
                continue
    return None


# ============================================================
# Comparadores por tipo
# ============================================================

def comparar_numero(resposta: str, esperado: float) -> bool:
    valor = extrair_primeiro_numero(resposta)
    if valor is None:
        return False
    return abs(valor - esperado) <= NUMERIC_TOLERANCE


def comparar_lista_strings(resposta: str, esperado: list[str]) -> bool:
    resposta_lower = resposta.lower()
    return all(item.lower() in resposta_lower for item in esperado)


def comparar_dict_numerico(resposta: str, esperado: dict) -> bool:
    """
    Verifica se cada par chave-valor do dicionário esperado aparece na resposta.
    Não exige ordem nem formato específico.
    """
    resposta_lower = resposta.lower()
    for chave, valor in esperado.items():
        if str(chave).lower() not in resposta_lower:
            return False
        # Procura o valor numérico próximo dessa chave
        # Heurística: pega um trecho ao redor da chave e procura número
        idx = resposta_lower.find(str(chave).lower())
        trecho = resposta[max(0, idx - 5): idx + 80]
        num = extrair_primeiro_numero(trecho)
        if num is None or abs(num - float(valor)) > NUMERIC_TOLERANCE * max(1.0, abs(valor)):
            return False
    return True


PALAVRAS_RECUSA = {
    "ambígua", "ambigua", "não entendi", "nao entendi",
    "esclarecer", "esclareça", "esclareca",
    "não consigo", "nao consigo",
    "não posso", "nao posso",
    "inválida", "invalida",
    "não está clara", "nao esta clara",
}


def comparar_categorica(resposta: str, esperado: str) -> bool:
    resposta_lower = resposta.lower()
    if esperado == "recusa":
        return any(palavra in resposta_lower for palavra in PALAVRAS_RECUSA)
    return esperado.lower() in resposta_lower


# ============================================================
# Comparador unificado
# ============================================================

def avaliar_resposta(resposta: str, esperado, tipo_resposta: str) -> bool:
    """
    Despacha para o comparador certo conforme o tipo da resposta esperada.
    Retorna True se a resposta é considerada correta.
    """
    if esperado is None:
        # Gabarito não foi preenchido — não dá para avaliar
        return False

    if tipo_resposta in ("numero_inteiro", "numero_float"):
        return comparar_numero(resposta, float(esperado))
    elif tipo_resposta == "lista_strings":
        return comparar_lista_strings(resposta, esperado)
    elif tipo_resposta == "dict_numerico":
        return comparar_dict_numerico(resposta, esperado)
    elif tipo_resposta == "categorica":
        return comparar_categorica(resposta, esperado)
    else:
        raise ValueError(f"Tipo de resposta desconhecido: {tipo_resposta}")


# ============================================================
# Agregação de métricas
# ============================================================

@dataclass
class BenchmarkSummary:
    """Resumo agregado da execução do benchmark."""
    total_perguntas: int
    acertos: int
    taxa_execucao_sucesso: float       # % de perguntas que terminaram sem crash
    acuracia_geral: float              # % de respostas corretas
    acuracia_por_tipo: dict[str, float]
    tool_calls_media: float
    latencia_media: float
    input_tokens_total: int
    output_tokens_total: int

    def imprimir(self):
        print("\n" + "=" * 60)
        print("RESUMO DO BENCHMARK")
        print("=" * 60)
        print(f"Total de perguntas:           {self.total_perguntas}")
        print(f"Acertos:                      {self.acertos}")
        print(f"Acurácia geral:               {self.acuracia_geral:.1%}")
        print(f"Taxa de execução bem-sucedida: {self.taxa_execucao_sucesso:.1%}")
        print()
        print("Acurácia por tipo de pergunta:")
        for tipo, acc in self.acuracia_por_tipo.items():
            print(f"  - {tipo:15s}: {acc:.1%}")
        print()
        print(f"Tool calls médias por pergunta: {self.tool_calls_media:.2f}")
        print(f"Latência média por pergunta:    {self.latencia_media:.2f}s")
        print(f"Tokens de entrada (total):      {self.input_tokens_total}")
        print(f"Tokens de saída (total):        {self.output_tokens_total}")
        print("=" * 60)
