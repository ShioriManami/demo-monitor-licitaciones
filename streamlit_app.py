"""Demo del monitor de licitaciones públicas de servicios de vigilancia.

Corre 100% con datos simulados de `demo_data/`: sin red, sin claves, sin IA en vivo.

    streamlit run streamlit_app.py
"""
from __future__ import annotations

import streamlit as st

from monitor_demo import consultas, ui
from monitor_demo.datos import DatasetInvalido
from monitor_demo.vistas import detalle, graficas, panorama, simulacion

st.set_page_config(
    page_title="Monitor de licitaciones · Demo",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

VISTAS = {
    "panorama": (":material/dashboard: Panorama", panorama.render),
    "detalle": (":material/folder_open: Detalle", detalle.render),
    "simular": (":material/play_circle: Simular corrida", simulacion.render),
    "graficas": (":material/bar_chart: Gráficas", graficas.render),
}

ui.aplicar_estilos()
ui.banner()

with st.container(key="encabezado", gap=None):
    st.title("Monitor de licitaciones públicas", anchor=False)
    st.caption("Servicios de seguridad privada · expedientes, clasificación de documentos y fichas técnicas")

try:
    dataset = consultas.dataset()
except DatasetInvalido as exc:
    ui.error_dataset(exc)
    st.stop()

# Navegación con un solo control: solo se ejecuta la vista elegida en cada rerun.
# La URL guarda la clave estable (?vista=detalle) para poder compartir enlaces.
if "vista" not in st.session_state:
    pedida = st.query_params.get("vista")
    st.session_state["vista"] = pedida if pedida in VISTAS else "panorama"


def _mantener_seleccion() -> None:
    """Evita que un segundo clic deje la navegación sin vista seleccionada."""
    if st.session_state["vista"] is None:
        st.session_state["vista"] = st.session_state.get("_ultima_vista", "panorama")


vista = st.segmented_control(
    "Vista",
    options=list(VISTAS),
    format_func=lambda clave: VISTAS[clave][0],
    key="vista",
    on_change=_mantener_seleccion,
    label_visibility="collapsed",
    width="stretch",
) or "panorama"
st.session_state["_ultima_vista"] = vista
if st.query_params.get("vista") != vista:
    st.query_params["vista"] = vista
if vista != "detalle" and "id" in st.query_params:
    del st.query_params["id"]
VISTAS[vista][1](dataset)
