import streamlit as st
import requests
import pandas as pd
import math

st.set_page_config(page_title="MCP Server - Natural Language to SQL", layout="wide")

# ----- CSS para compactar y centrar tabla, ocultar Deploy, layout responsive -----
st.markdown("""
<style>
header [data-testid="stHeader"] div span {display: none !important;}
header [data-testid="stHeader"] > div:nth-child(2) {display: none !important;}
header [data-testid="stHeader"] > div [data-testid="stToolbar"] {right: 2em !important;}
.botones-pegados button { margin-right: 0.5em !important; }
.result-table {
    font-size: 0.85em;
    border-collapse: collapse;
    min-width: 150px;
}
.result-table th, .result-table td {
    text-align: center !important;
    vertical-align: middle !important;
    padding: 4px 10px !important;
    border: 1px solid #222;
    background: #18191A;
    color: #f2f2f2;
}
.result-table th {
    background: #22232a;
    font-weight: bold;
}
@media (max-width: 900px) {
    div[data-testid="stHorizontalBlock"] > div {width: 100% !important;}
}
.no-horizontal-scroll pre {
    white-space: pre-wrap !important;
    word-break: break-word !important;
    overflow-x: auto;
}
</style>
""", unsafe_allow_html=True)

st.title("MCP Server - Natural Language to SQL")

# ---- Session State ----
if "history" not in st.session_state:
    st.session_state["history"] = []
if "pending_query" not in st.session_state:
    st.session_state["pending_query"] = ""
if "last_sql" not in st.session_state:
    st.session_state["last_sql"] = None
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_columns" not in st.session_state:
    st.session_state["last_columns"] = None
if "last_error" not in st.session_state:
    st.session_state["last_error"] = None
if "run_query_once" not in st.session_state:
    st.session_state["run_query_once"] = False

# ---- Layout en dos columnas principales ----
col1, col2 = st.columns([2, 3])

with col1:
    user_input = st.text_input(
        "Escribe tu consulta en lenguaje natural:",
        key="consulta_text",
        value=st.session_state["pending_query"],
        placeholder="Ejemplo: Muéstrame todos los usuarios registrados"
    )
    # Botones en fila horizontal
    with st.container():
        st.markdown(
            '<div class="botones-pegados" style="display:flex;gap:0.5em;">',
            unsafe_allow_html=True
        )
        ejecutar = st.button("🚀 Ejecutar consulta", key="ejecutar_query")
        borrar = st.button("🧹 Borrar consulta", key="borrar_query")
        st.markdown('</div>', unsafe_allow_html=True)

    if borrar:
        st.session_state["pending_query"] = ""
        st.rerun()

    if user_input:
        st.session_state["pending_query"] = user_input

    if user_input and (ejecutar or st.session_state["run_query_once"]):
        with st.spinner('Consultando...'):
            try:
                response = requests.post(
                    "http://localhost:8001/mcp/query",
                    json={"question": user_input}
                )
                if response.status_code != 200:
                    try:
                        error_message = response.json().get("detail", "")
                    except Exception:
                        error_message = response.text
                    st.session_state["last_sql"] = None
                    st.session_state["last_result"] = None
                    st.session_state["last_columns"] = None
                    st.session_state["last_error"] = error_message
                else:
                    data = response.json()
                    st.session_state["last_sql"] = data.get('sql', '')
                    st.session_state["last_result"] = data.get('result', {}).get('rows', [])
                    st.session_state["last_columns"] = data.get('result', {}).get('columns', [])
                    st.session_state["last_error"] = None
                    if not st.session_state["history"] or (
                        user_input != st.session_state["history"][-1]["question"]
                    ):
                        st.session_state["history"].append({
                            "question": user_input,
                            "sql": st.session_state["last_sql"]
                        })
            except Exception as e:
                st.session_state["last_sql"] = None
                st.session_state["last_result"] = None
                st.session_state["last_columns"] = None
                st.session_state["last_error"] = f"❌ Ocurrió un error inesperado: {e}"
        st.session_state["run_query_once"] = False

    # SQL generada (wrap, nunca scroll horizontal)
    if st.session_state["last_sql"]:
        st.markdown("#### Consulta SQL generada")
        st.markdown('<div class="no-horizontal-scroll">', unsafe_allow_html=True)
        st.code(st.session_state["last_sql"], language="sql")
        st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state["last_error"]:
        st.error(st.session_state["last_error"])

with col2:
    if st.session_state["last_result"] is not None:
        st.subheader("Resultado")
        if st.session_state["last_result"]:
            # Renderiza tabla como HTML SIEMPRE compacta y centrada
            if st.session_state["last_columns"]:
                df = pd.DataFrame(st.session_state["last_result"], columns=st.session_state["last_columns"])
                st.markdown(df.to_html(classes="result-table", index=False), unsafe_allow_html=True)
            else:
                # Solo una columna (ej: COUNT(*))
                df = pd.DataFrame(st.session_state["last_result"])
                st.markdown(df.to_html(classes="result-table", index=False, header=False), unsafe_allow_html=True)
        else:
            st.info("La consulta no devolvió resultados.")

# ---- Historial de consultas (agrupado en filas de 10 columnas) ----
st.markdown("---")
st.markdown("### Historial de consultas realizadas")
if st.session_state["history"]:
    if st.button("🗑️ Borrar historial de consultas"):
        st.session_state["history"] = []
        st.rerun()
    num_per_row = 10
    history = st.session_state["history"]
    num_rows = math.ceil(len(history) / num_per_row)
    for i in range(num_rows):
        cols = st.columns(num_per_row)
        for j in range(num_per_row):
            idx = i * num_per_row + j
            if idx < len(history):
                with cols[j]:
                    if st.button(history[idx]["question"], key=f"hist_{idx}"):
                        st.session_state["pending_query"] = history[idx]["question"]
                        st.session_state["run_query_once"] = True
                        st.rerun()
else:
    st.info("No hay consultas en el historial.")