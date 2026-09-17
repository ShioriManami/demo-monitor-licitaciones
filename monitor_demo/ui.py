"""Piezas de interfaz compartidas: estilos, banner, formatos y badges."""
from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from monitor_demo.datos import DatasetInvalido, DocumentoDemo
from monitor_demo.esquemas import FichaTecnica

BANNER = "Demo con datos simulados: no consulta portales reales ni usa modelos de IA en vivo."
CREDITO_NOMBRE = "Alan Mendoza"
CREDITO_URL = "https://portafolio-ki87.vercel.app"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

_CSS = """
<style>
  [data-testid="stMainBlockContainer"] { padding-top: 3.25rem; padding-bottom: 3rem; max-width: 1240px; }
  .st-key-demo-banner {
    background: rgba(73, 145, 229, 0.10);
    border: 1px solid rgba(73, 145, 229, 0.45);
    border-radius: 0.75rem;
    padding: 0.6rem 1rem;
  }
  .st-key-demo-banner [data-testid="stMarkdownContainer"],
  .st-key-encabezado [data-testid="stMarkdownContainer"],
  .st-key-encabezado [data-testid="stCaptionContainer"] { margin-bottom: 0; }
  .st-key-demo-banner p, .st-key-encabezado p { margin: 0; }
  .st-key-demo-banner p { font-size: 0.92rem; }
  .st-key-encabezado h1 { font-size: 1.65rem; padding: 0.35rem 0 0.1rem; }
  /* Filas de métricas y tarjetas que se reparten en 2 columnas en móvil */
  [class*="st-key-metricas"] > *, .st-key-etapas > * { flex: 1 1 9.5rem; min-width: 9.5rem; }
  [class*="st-key-punto-riesgo"] { border-left: 3px solid #e66767; padding-left: 0.8rem; }
  [class*="st-key-punto-oportunidad"] { border-left: 3px solid #0ca30c; padding-left: 0.8rem; }
  [class*="st-key-punto-observacion"] { border-left: 3px solid #4991e5; padding-left: 0.8rem; }
  [class*="st-key-etapa-"] { background: rgba(255, 255, 255, 0.02); }
  [data-testid="stMetricLabel"] p { font-size: 0.85rem; }
</style>
"""


def aplicar_estilos() -> None:
    st.html(_CSS)


def banner() -> None:
    with st.container(key="demo-banner", horizontal=True, vertical_alignment="center", gap="small"):
        st.markdown(f":material/science: **{BANNER}**", width="stretch")
        st.markdown(f"Diseño y desarrollo: [{CREDITO_NOMBRE}]({CREDITO_URL})", width="content")


def error_dataset(exc: DatasetInvalido) -> None:
    st.error(
        "La demo se detuvo para no mostrar datos inconsistentes. Corregí los archivos de `demo_data/` "
        "y recargá la página.",
        title=f"El dataset simulado no es válido ({exc.origen})",
        icon=":material/error:",
    )
    st.markdown(f"**{len(exc.errores)} error(es) de validación:**")
    st.code("\n".join(f"• {err}" for err in exc.errores[:60]), language=None, wrap_lines=True)


# ---------------- formatos ----------------


def fecha(valor: date | datetime | None) -> str:
    if valor is None:
        return "—"
    return f"{valor.day} {MESES[valor.month - 1]} {valor.year}"


def fecha_hora(valor: datetime | None) -> str:
    if valor is None:
        return "—"
    return f"{fecha(valor)} · {valor:%H:%M}"


def mxn(valor: float | None) -> str:
    return "—" if valor is None else f"${valor:,.0f}"


def mxn_compacto(valor: float | None) -> str:
    if valor is None:
        return "—"
    return f"${valor / 1_000_000:,.1f} M"


def num(valor: float | int | None, sufijo: str = "") -> str:
    """Número sin ceros de relleno: 10.0 → '10', 2.5 → '2.5'."""
    return "—" if valor is None else f"{valor:g}{sufijo}"


def plural(cantidad: int, singular: str, plural_: str) -> str:
    return f"{cantidad} {singular if cantidad == 1 else plural_}"


def si_no(valor: bool | None) -> str:
    return {True: "Sí", False: "No", None: "—"}[valor]


def o(valor: object, sufijo: str = "") -> str:
    if valor is None or valor == "" or valor == []:
        return "—"
    return f"{valor}{sufijo}"


# ---------------- badges ----------------


def veredicto(ficha: FichaTecnica) -> tuple[str, str, str]:
    """(etiqueta, color de badge, icono) según la evaluación de la ficha."""
    return {
        True: ("Factible", "green", ":material/check_circle:"),
        False: ("No factible", "red", ":material/cancel:"),
        None: ("Indeterminado", "orange", ":material/help:"),
    }[ficha.evaluacion.cumplimos_requisitos]


def badge_clasificacion(doc: DocumentoDemo) -> None:
    if doc.escaneado:
        st.badge("Escaneado · OCR", icon=":material/document_scanner:", color="orange")
    else:
        st.badge("Texto", icon=":material/article:", color="blue")


# ---------------- navegación ----------------


def ir_a_detalle(id_expediente: str) -> None:
    """Callback: cambia a la vista de detalle con el expediente elegido."""
    st.session_state["vista"] = "detalle"
    st.session_state["id"] = id_expediente
