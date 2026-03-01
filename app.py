"""
app.py — Interfaz Streamlit con medición de huella de carbono
"""

import sys
import os
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python code"))
from analyst_agent  import chat, extract_kpis
from reporter_agent import generate_report
from carbon_tracker import CarbonTracker

# ── Configuración ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Agentic Analytics ESG",
    page_icon="🌿",
    layout="wide",
)

st.markdown("<style>.block-container{padding-top:2rem}</style>", unsafe_allow_html=True)

st.title("🌿 Agentic Analytics ESG")
st.caption("Consulta los datos de sostenibilidad y genera el informe automáticamente.")

tab_chat, tab_report = st.tabs(["💬 Analista ESG", "📄 Generar Informe"])


# ── Helper: panel de huella de carbono ───────────────────────────────────────

def _render_carbon_panel(summary: dict):
    """Muestra el desglose de huella de carbono en Streamlit."""

    PHASE_ICONS = {"chat": "💬", "kpis": "📊", "pdf": "📄"}

    st.markdown("---")
    st.markdown("### 🌱 Huella de carbono de esta operación")

    # Fila de fases
    cols = st.columns(len(summary["phases"]) + 1)

    for i, phase in enumerate(summary["phases"]):
        icon  = PHASE_ICONS.get(phase["name"], "⚙️")
        label = phase["name"].upper()
        with cols[i]:
            st.metric(
                label=f"{icon} {label}",
                value=f"{phase['total_g_co2']:.4f} g CO₂",
                help=(
                    f"Local (CPU): {phase['local_g_co2']:.6f} g CO₂\n"
                    f"API (tokens): {phase['api_g_co2']:.6f} g CO₂\n"
                    f"Tokens entrada: {phase['input_tokens']:,}\n"
                    f"Tokens salida: {phase['output_tokens']:,}"
                )
            )

    with cols[-1]:
        st.metric(
            label="⚡ TOTAL",
            value=f"{summary['total_g_co2']:.4f} g CO₂",
        )

    # Equivalencias
    st.caption(
        f"Equivale a **{summary['equiv_km_car']:.4f} km en coche** "
        f"o **{summary['equiv_phone_pct']:.2f}%** de cargar un móvil"
    )

    # Desglose detallado expandible
    with st.expander("Ver desglose detallado"):
        for phase in summary["phases"]:
            icon = PHASE_ICONS.get(phase["name"], "⚙️")
            st.markdown(f"**{icon} {phase['name'].upper()}**")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"🖥️ Local: `{phase['local_g_co2']:.6f}` g CO₂")
            c2.markdown(f"☁️ API: `{phase['api_g_co2']:.6f}` g CO₂")
            c3.markdown(f"🔤 Tokens: `{phase['input_tokens']:,}` in / `{phase['output_tokens']:,}` out")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHATBOT
# ══════════════════════════════════════════════════════════════════════════════

with tab_chat:

    st.subheader("Analista ESG")
    st.write("Pregunta sobre consumo eléctrico, agua, residuos o cualquier métrica.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("¿Qué quieres saber sobre los datos ESG?"):

        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Consultando la base de datos..."):

                # ── Medición de huella ────────────────────────────────────
                tracker = CarbonTracker()
                tracker.start("chat")
                response = chat(user_input, tracker=tracker)
                tracker.stop(
                    input_tokens  = getattr(tracker, "_last_input_tokens",  0),
                    output_tokens = getattr(tracker, "_last_output_tokens", 0),
                )
                carbon_summary = tracker.get_summary()
                # ─────────────────────────────────────────────────────────

            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        # Panel de huella
        _render_carbon_panel(carbon_summary)

    if st.session_state.messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.messages = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GENERACIÓN DE INFORME
# ══════════════════════════════════════════════════════════════════════════════

with tab_report:

    st.subheader("Generación de Informe")
    st.write("El agente extrae los KPIs y genera el informe en PDF y HTML.")

    period = st.text_input("Periodo", value="2024", placeholder="Ej: 2023, 2024...")

    if st.button("⚙️ Generar informe", type="primary", disabled=not period):

        tracker = CarbonTracker()

        with st.status("Generando informe...", expanded=True) as status:

            # Fase 1: KPIs
            st.write("📊 Extrayendo KPIs...")
            tracker.start("kpis")
            try:
                kpis = extract_kpis(period, tracker=tracker)
            except Exception as e:
                st.error(f"Error extrayendo KPIs: {e}")
                st.stop()
            tracker.stop(
                input_tokens  = getattr(tracker, "_last_input_tokens",  0),
                output_tokens = getattr(tracker, "_last_output_tokens", 0),
            )
            st.write("✅ KPIs extraídos")

            # Fase 2: PDF
            st.write("📄 Generando informe...")
            tracker.start("pdf")
            try:
                paths = generate_report(kpis, tracker=tracker)
            except Exception as e:
                st.error(f"Error generando informe: {e}")
                st.stop()
            tracker.stop(input_tokens=0, output_tokens=0)
            st.write("✅ Informe generado")

            status.update(label="Informe listo ✅", state="complete")

        # KPIs resumen
        st.markdown("---")
        st.info(kpis["executive_summary"])

        col1, col2, col3 = st.columns(3)
        with col1:
            k = kpis["kpis"]["consumo_electrico"]
            icon = {"mejora": "🟢", "empeora": "🔴", "estable": "🟡"}.get(k["trend"], "⚪")
            st.metric("⚡ Consumo eléctrico", f"{k['total_kwh']:,.0f} kWh", f"{icon} {k['trend']}")
        with col2:
            k = kpis["kpis"]["agua"]
            icon = {"mejora": "🟢", "empeora": "🔴", "estable": "🟡"}.get(k["trend"], "⚪")
            total_agua = k.get("total_litros") or k.get("total_m3") or 0
            st.metric("💧 Agua", f"{total_agua:,.0f} L", f"{icon} {k['trend']}")
        with col3:
            k = kpis["kpis"]["residuos"]
            icon = {"mejora": "🟢", "empeora": "🔴", "estable": "🟡"}.get(k["trend"], "⚪")
            st.metric("♻️ Residuos", f"{k['total_tons'] or 0:,.1f} t", f"{icon} {k['trend']}")

        # Botones de descarga
        st.markdown("---")
        col_pdf, col_html = st.columns(2)
        with col_pdf:
            with open(paths["pdf"], "rb") as f:
                st.download_button(
                    "⬇️ Descargar PDF", f,
                    file_name=f"informe_esg_{period.replace(' ','_')}.pdf",
                    mime="application/pdf", type="primary", use_container_width=True,
                )
        with col_html:
            with open(paths["html"], "rb") as f:
                st.download_button(
                    "🌐 Descargar HTML", f,
                    file_name=f"informe_esg_{period.replace(' ','_')}.html",
                    mime="text/html", use_container_width=True,
                )

        # Panel de huella de carbono
        _render_carbon_panel(tracker.get_summary())