import streamlit as st
from pathlib import Path
from agent import Agent
from tools import state
from config import DATASET_PATH

OUTPUTS_DIR = Path("outputs")

# -----------------------------
# Tema Fórmula 1 — CSS injetado
# -----------------------------
F1_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@400;500;600&family=Share+Tech+Mono&display=swap');

html, body, [data-testid="stApp"] {
    background-color: #0d0d0d !important;
    color: #f0f0f0 !important;
    font-family: 'Barlow', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #111 !important;
    border-right: 1px solid #2a2a2a;
}
[data-testid="stHeader"] { background: transparent !important; }

h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 900 !important;
    font-size: 2.6rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    color: #ffffff !important;
    line-height: 1 !important;
    padding-bottom: 0.25rem !important;
    border-bottom: 3px solid #e8002d !important;
    margin-bottom: 1.5rem !important;
}
h2, h3 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
.f1-subtitle {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    color: #e8002d;
    text-transform: uppercase;
    margin-top: -1.2rem;
    margin-bottom: 1.8rem;
}

[data-testid="stChatMessageContent"] {
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}
[data-testid="stChatMessage"][data-role="user"] {
    background: #1a1a1a !important;
    border-left: 3px solid #e8002d !important;
    border-radius: 2px !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stChatMessage"][data-role="assistant"] {
    background: #151515 !important;
    border-left: 3px solid #ff6b00 !important;
    border-radius: 2px !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
    background-color: #e8002d !important;
}
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
    background-color: #ff6b00 !important;
}

[data-testid="stChatInput"] textarea {
    background-color: #1c1c1c !important;
    color: #f0f0f0 !important;
    border: 1px solid #333 !important;
    border-radius: 2px !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.95rem !important;
    caret-color: #e8002d !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #e8002d !important;
    box-shadow: 0 0 0 2px rgba(232,0,45,0.15) !important;
}
[data-testid="stChatInput"] button {
    background-color: #e8002d !important;
    border-radius: 2px !important;
}
[data-testid="stChatInput"] button:hover { background-color: #c4001f !important; }

[data-testid="stCaptionContainer"], .stCaption {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    color: #888 !important;
    letter-spacing: 0.08em !important;
    border-top: 1px solid #2a2a2a !important;
    padding-top: 0.4rem !important;
    margin-top: 0.6rem !important;
}

[data-testid="stMetric"] {
    background: #151515 !important;
    border: 1px solid #2a2a2a !important;
    border-top: 3px solid #e8002d !important;
    border-radius: 2px !important;
    padding: 0.75rem 1rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #888 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
    color: #ffffff !important;
}

[data-testid="stExpander"] {
    background: #111 !important;
    border: 1px solid #2a2a2a !important;
    border-left: 3px solid #e8002d !important;
    border-radius: 2px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #e8002d !important;
}

.cmd-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 6px 16px;
    margin-top: 8px;
}
.cmd-key {
    font-family: 'Share Tech Mono', monospace;
    color: #e8002d;
    font-size: 0.85rem;
    background: #1e0007;
    border: 1px solid #e8002d33;
    padding: 2px 8px;
    border-radius: 2px;
    align-self: center;
}
.cmd-desc {
    font-family: 'Barlow', sans-serif;
    font-size: 0.88rem;
    color: #bbb;
    align-self: center;
}

[data-testid="stImage"] {
    border: 1px solid #2a2a2a !important;
    border-radius: 2px !important;
    margin-top: 0.75rem !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #e8002d; }

hr { border-color: #2a2a2a !important; margin: 1rem 0 !important; }

[data-testid="stAlert"] {
    border-left: 4px solid #e8002d !important;
    background: #1a0005 !important;
    border-radius: 2px !important;
}
</style>
"""

# ══════════════════════════════════════════════
# Inicialização
# ══════════════════════════════════════════════
if "init" not in st.session_state:
    if not Path(DATASET_PATH).exists():
        st.error(f"Dataset não encontrado em {DATASET_PATH}")
        st.stop()
    state.load(str(DATASET_PATH))
    st.session_state.agent = Agent()
    st.session_state.messages = []
    st.session_state.ultima_resposta = None
    st.session_state.custo = {"input": 0, "output": 0, "latencia": 0.0, "tool_calls": 0}
    OUTPUTS_DIR.mkdir(exist_ok=True)
    st.session_state.outputs_vistos = (
        set(p.name for p in OUTPUTS_DIR.glob("*.png"))
        | set(p.name for p in OUTPUTS_DIR.glob("*.jpg"))
    )
    st.session_state.init = True

agent = st.session_state.agent
st.markdown(F1_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════
def coletar_imagens_novas() -> list[Path]:
    atuais = (
        set(p.name for p in OUTPUTS_DIR.glob("*.png"))
        | set(p.name for p in OUTPUTS_DIR.glob("*.jpg"))
    )
    novas = atuais - st.session_state.outputs_vistos
    st.session_state.outputs_vistos = atuais
    return sorted(OUTPUTS_DIR / nome for nome in novas)


def render_ajuda():
    with st.expander("📋 COMANDOS DISPONÍVEIS", expanded=True):
        st.markdown(
            """
            <div class="cmd-grid">
                <span class="cmd-key">/ajuda</span>
                <span class="cmd-desc">Lista todos os comandos especiais</span>
                <span class="cmd-key">/trajetoria</span>
                <span class="cmd-desc">Passo a passo da última pergunta (tool calls, LLM, resultados)</span>
                <span class="cmd-key">/custo</span>
                <span class="cmd-desc">Tokens e latência acumulados na sessão</span>
                <span class="cmd-key">/sair</span>
                <span class="cmd-desc">Limpa o histórico e reinicia a sessão</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_trajetoria(resultado):
    if resultado is None:
        with st.expander("🔍 TRAJETÓRIA", expanded=True):
            st.warning("Nenhuma trajetória disponível — faça uma pergunta primeiro.")
        return

    linhas = []
    for i, passo in enumerate(resultado.trajetoria, start=1):
        if passo.tipo == "llm_text":
            conteudo = passo.conteudo[:140] + ("…" if len(passo.conteudo) > 140 else "")
        elif passo.tipo == "tool_call":
            args_str = ", ".join(
                f"{k}={v}" for k, v in passo.conteudo["argumentos"].items()
            )
            conteudo = f"{passo.conteudo['nome']}({args_str})"
        else:
            conteudo = str(passo.conteudo)[:140]
        linhas.append({"#": i, "Tipo": passo.tipo, "Conteúdo": conteudo})

    titulo = resultado.pergunta[:70] + ("…" if len(resultado.pergunta) > 70 else "")
    with st.expander(f"🔍 TRAJETÓRIA — {titulo.upper()}", expanded=True):
        st.table(linhas)


def render_custo(snapshot: dict | None = None):
    c = snapshot if snapshot else st.session_state.custo
    total = c["input"] + c["output"]
    with st.expander("⚡ TELEMETRIA DA SESSÃO", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tokens entrada", f"{c['input']:,}")
        col2.metric("Tokens saída", f"{c['output']:,}")
        col3.metric("Tool calls", str(c["tool_calls"]))
        col4.metric("Latência total", f"{c['latencia']:.2f}s")
        st.caption(f"Total de tokens consumidos na sessão: {total:,}")


COMANDOS = {"/ajuda", "/trajetoria", "/custo", "/sair"}

# ══════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════
st.markdown("# 🏎 Agente EDA")
st.markdown(
    '<p class="f1-subtitle">▶ RACE DATA INTELLIGENCE — PIT WALL ANALYTICS</p>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════
# Histórico do chat
# ══════════════════════════════════════════════
for msg in st.session_state.messages:
    if msg.get("role") == "command":
        cmd = msg["cmd"]
        if cmd == "/ajuda":
            render_ajuda()
        elif cmd == "/trajetoria":
            render_trajetoria(msg.get("resultado"))
        elif cmd == "/custo":
            render_custo(snapshot=msg.get("snapshot"))
        continue

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for img_path in msg.get("imagens", []):
            st.image(img_path, use_container_width=True)

# ══════════════════════════════════════════════
# Input
# ══════════════════════════════════════════════
pergunta = st.chat_input("Pergunte sobre os dados ou use /ajuda...")

# ══════════════════════════════════════════════
# Processamento
# ══════════════════════════════════════════════
if pergunta:
    entrada = pergunta.strip()

    # ── Comandos especiais ──────────────────────
    if entrada in COMANDOS:
        with st.chat_message("user"):
            st.markdown(f"`{entrada}`")

        if entrada == "/sair":
            st.session_state.messages = []
            st.session_state.ultima_resposta = None
            st.session_state.custo = {"input": 0, "output": 0, "latencia": 0.0, "tool_calls": 0}
            st.rerun()

        elif entrada == "/ajuda":
            render_ajuda()
            st.session_state.messages.append({"role": "command", "cmd": "/ajuda"})

        elif entrada == "/trajetoria":
            render_trajetoria(st.session_state.ultima_resposta)
            st.session_state.messages.append({
                "role": "command",
                "cmd": "/trajetoria",
                "resultado": st.session_state.ultima_resposta,
            })

        elif entrada == "/custo":
            render_custo()
            st.session_state.messages.append({
                "role": "command",
                "cmd": "/custo",
                "snapshot": dict(st.session_state.custo),
            })

    # ── Pergunta normal ─────────────────────────
    else:
        st.session_state.messages.append({"role": "user", "content": entrada})
        with st.chat_message("user"):
            st.markdown(entrada)

        with st.chat_message("assistant"):
            with st.spinner("Analisando telemetria..."):
                resultado = agent.perguntar(entrada)

            st.session_state.ultima_resposta = resultado

            st.session_state.custo["input"] += resultado.input_tokens
            st.session_state.custo["output"] += resultado.output_tokens
            st.session_state.custo["latencia"] += resultado.latencia_total
            st.session_state.custo["tool_calls"] += resultado.total_tool_calls

            st.markdown(resultado.resposta_final)

            imagens_novas = coletar_imagens_novas()
            for img_path in imagens_novas:
                st.image(str(img_path), use_container_width=True)

            st.caption(
                f"🛠 {resultado.total_tool_calls} tool calls  ·  "
                f"⏱ {resultado.latencia_total:.2f}s  ·  "
                f"🔢 {resultado.input_tokens + resultado.output_tokens} tokens"
            )

        st.session_state.messages.append({
            "role": "assistant",
            "content": resultado.resposta_final,
            "imagens": [str(p) for p in imagens_novas],
        })