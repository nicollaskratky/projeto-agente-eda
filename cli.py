import streamlit as st
from pathlib import Path
from agent import Agent
from tools import state
from config import DATASET_PATH

OUTPUTS_DIR = Path("outputs")

# -----------------------------
# Inicialização
# -----------------------------
if "init" not in st.session_state:
    if not Path(DATASET_PATH).exists():
        st.error(f"Dataset não encontrado em {DATASET_PATH}")
        st.stop()
    state.load(str(DATASET_PATH))
    st.session_state.agent = Agent()
    st.session_state.messages = []  # histórico do chat
    st.session_state.ultima_resposta = None
    st.session_state.custo = {
        "input": 0,
        "output": 0,
        "latencia": 0.0,
        "tool_calls": 0
    }
    # snapshot dos arquivos já existentes em outputs/
    OUTPUTS_DIR.mkdir(exist_ok=True)
    st.session_state.outputs_vistos = set(
        p.name for p in OUTPUTS_DIR.glob("*.png")
    ) | set(p.name for p in OUTPUTS_DIR.glob("*.jpg"))
    st.session_state.init = True

agent = st.session_state.agent

# -----------------------------
# Helper: imagens novas desde o último turno
# -----------------------------
def coletar_imagens_novas() -> list[Path]:
    """Retorna imagens em outputs/ que ainda não foram exibidas."""
    atuais = set(
        p.name for p in OUTPUTS_DIR.glob("*.png")
    ) | set(p.name for p in OUTPUTS_DIR.glob("*.jpg"))
    novas = atuais - st.session_state.outputs_vistos
    st.session_state.outputs_vistos = atuais
    return sorted(OUTPUTS_DIR / nome for nome in novas)

# -----------------------------
# Header
# -----------------------------
st.title("📊 Agente EDA")

# -----------------------------
# Render do histórico (ChatGPT style)
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # re-renderiza imagens salvas junto com a mensagem
        for img_path in msg.get("imagens", []):
            st.image(img_path)

# -----------------------------
# Input do usuário
# -----------------------------
pergunta = st.chat_input("Pergunte algo sobre o dataset...")

# -----------------------------
# Quando usuário envia mensagem
# -----------------------------
if pergunta:
    # 1. Mostra mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # 2. Processa agente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resultado = agent.perguntar(pergunta)

        st.session_state.ultima_resposta = resultado

        # atualiza custo
        st.session_state.custo["input"] += resultado.input_tokens
        st.session_state.custo["output"] += resultado.output_tokens
        st.session_state.custo["latencia"] += resultado.latencia_total
        st.session_state.custo["tool_calls"] += resultado.total_tool_calls

        # resposta final
        st.markdown(resultado.resposta_final)
        st.caption(
            f"🛠 {resultado.total_tool_calls} tool calls · "
            f"⏱ {resultado.latencia_total:.2f}s · "
            f"🔢 {resultado.input_tokens + resultado.output_tokens} tokens"
        )

        # exibe imagens geradas neste turno
        imagens_novas = coletar_imagens_novas()
        for img_path in imagens_novas:
            st.image(str(img_path), use_container_width=True)

    # salva no histórico (com referência às imagens para re-render)
    st.session_state.messages.append({
        "role": "assistant",
        "content": resultado.resposta_final,
        "imagens": [str(p) for p in imagens_novas],
    })