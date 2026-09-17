"""Vista 4: gráficas construidas con el dataset simulado.

Solo se ejecuta cuando esta vista está activa; los DataFrames vienen de
`consultas.datos_graficas()` (cacheado).
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from monitor_demo import consultas
from monitor_demo.datos import Dataset

SUPERFICIE = "#0f1520"
# Paleta categórica validada contra la superficie oscura (CVD y contraste).
COLOR_CLASIFICACION = {"Texto": "#4991e5", "Escaneado": "#d95926"}
COLOR_ETAPA = {
    "Descarga (simulada)": "#3987e5",
    "Clasificación texto/escaneado": "#199e70",
    "OCR selectivo": "#d95926",
    "Extracción de texto": "#9085e9",
    "Ficha técnica": "#c98500",
}
ALTO_FILA = 26
ALTO_FILA_TIPO = 40
EXTRA_EJES = 90  # leyenda superior + eje x con título


def render(ds: Dataset) -> None:
    datos = consultas.datos_graficas()
    docs, tiempos = datos["docs"], datos["tiempos"]

    st.subheader("Gráficas del dataset simulado", anchor=False)
    st.caption("Todas las cifras salen de `demo_data/`: son sintéticas y sirven para ilustrar el flujo.")

    escaneados = int((docs["clasificacion"] == "Escaneado").sum())
    paginas_ocr = int(docs.loc[docs["clasificacion"] == "Escaneado", "paginas"].sum())
    total_seg = float(tiempos["segundos"].sum())
    seg_ocr = float(tiempos.loc[tiempos["etapa"] == "OCR selectivo", "segundos"].sum())
    with st.container(horizontal=True, gap="small", key="metricas-graficas"):
        st.metric("Documentos", len(docs), border=True)
        st.metric("Escaneados", f"{escaneados} · {escaneados / len(docs):.0%}", border=True)
        st.metric("Páginas con OCR", f"{paginas_ocr} de {int(docs['paginas'].sum()):,}", border=True)
        st.metric("Tiempo simulado total", f"{total_seg / 60:.1f} min", border=True,
                  help=f"El OCR representa el {seg_ocr / total_seg:.0%} del tiempo aunque solo toca a los escaneados")

    ids = [e.id for e in ds.expedientes]
    izquierda, derecha = st.columns([1.15, 1], gap="medium")
    with izquierda:
        with st.container(border=True):
            st.markdown("**Documentos por expediente**  \n:gray[Cantidad de anexos, separados en texto y escaneados]")
            st.altair_chart(_barras_documentos(datos["por_expediente"], ids), width="stretch",
                            height=len(ids) * ALTO_FILA + EXTRA_EJES)
            _tabla_opcional("tabla-docs", datos["por_expediente"].pivot_table(
                index="expediente", columns="clasificacion", values="documentos", fill_value=0).reset_index())
    with derecha:
        with st.container(border=True):
            st.markdown("**Texto vs escaneado por tipo de documento**  \n:gray[Qué anexos suelen llegar sin capa de texto]")
            tipos = datos["por_tipo"]["tipo"].nunique()
            st.altair_chart(_barras_tipo(datos["por_tipo"]), width="stretch",
                            height=tipos * ALTO_FILA_TIPO + EXTRA_EJES)
            _tabla_opcional("tabla-tipos", datos["por_tipo"].pivot_table(
                index="tipo", columns="clasificacion", values="documentos", fill_value=0).reset_index())

    with st.container(border=True):
        st.markdown("**Tiempos simulados de procesamiento por expediente**  \n"
                    ":gray[Segundos por etapa: el OCR solo aparece donde hay escaneados]")
        st.altair_chart(_barras_tiempos(tiempos, ids), width="stretch", height=len(ids) * ALTO_FILA + EXTRA_EJES)
        _tabla_opcional("tabla-tiempos", tiempos.pivot_table(
            index="expediente", columns="etapa", values="segundos", fill_value=0).reset_index())


def _tabla_opcional(clave: str, tabla: pd.DataFrame) -> None:
    expander = st.expander("Ver datos en tabla", icon=":material/table:", key=clave, on_change="rerun")
    if expander.open:
        with expander:
            st.dataframe(tabla, hide_index=True)


def _leyenda() -> alt.Legend:
    return alt.Legend(title=None, orient="top", direction="horizontal", symbolType="square", labelLimit=220)


def _barras_documentos(df: pd.DataFrame, ids: list[str]) -> alt.Chart:
    df = df.assign(orden=df["clasificacion"].map({"Texto": 0, "Escaneado": 1}))
    return (
        alt.Chart(df)
        .mark_bar(size=16, stroke=SUPERFICIE, strokeWidth=2)
        .encode(
            y=alt.Y("expediente:N", sort=ids, title=None, axis=alt.Axis(labelLimit=140)),
            x=alt.X("documentos:Q", stack="zero", title="Documentos", axis=alt.Axis(tickMinStep=1, format="d")),
            color=alt.Color("clasificacion:N", legend=_leyenda(),
                            scale=alt.Scale(domain=list(COLOR_CLASIFICACION), range=list(COLOR_CLASIFICACION.values()))),
            order=alt.Order("orden:Q"),
            tooltip=[alt.Tooltip("expediente:N", title="Expediente"),
                     alt.Tooltip("clasificacion:N", title="Clasificación"),
                     alt.Tooltip("documentos:Q", title="Documentos")],
        )
        .properties(height=len(ids) * ALTO_FILA)
    )


def _barras_tipo(df: pd.DataFrame) -> alt.Chart:
    orden_tipos = df.groupby("tipo")["documentos"].sum().sort_values(ascending=False).index.tolist()
    df = df.assign(orden=df["clasificacion"].map({"Texto": 0, "Escaneado": 1}))
    return (
        alt.Chart(df)
        .mark_bar(size=18, stroke=SUPERFICIE, strokeWidth=2)
        .encode(
            y=alt.Y("tipo:N", sort=orden_tipos, title=None, axis=alt.Axis(labelLimit=220)),
            x=alt.X("documentos:Q", stack="zero", title="Documentos", axis=alt.Axis(tickMinStep=1, format="d")),
            color=alt.Color("clasificacion:N", legend=_leyenda(),
                            scale=alt.Scale(domain=list(COLOR_CLASIFICACION), range=list(COLOR_CLASIFICACION.values()))),
            order=alt.Order("orden:Q"),
            tooltip=[alt.Tooltip("tipo:N", title="Tipo"),
                     alt.Tooltip("clasificacion:N", title="Clasificación"),
                     alt.Tooltip("documentos:Q", title="Documentos")],
        )
        .properties(height=len(orden_tipos) * ALTO_FILA_TIPO)
    )


def _barras_tiempos(df: pd.DataFrame, ids: list[str]) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(size=16, stroke=SUPERFICIE, strokeWidth=2)
        .encode(
            y=alt.Y("expediente:N", sort=ids, title=None, axis=alt.Axis(labelLimit=140)),
            x=alt.X("segundos:Q", stack="zero", title="Segundos simulados"),
            color=alt.Color("etapa:N", legend=_leyenda(),
                            scale=alt.Scale(domain=list(COLOR_ETAPA), range=list(COLOR_ETAPA.values()))),
            order=alt.Order("orden:Q"),
            tooltip=[alt.Tooltip("expediente:N", title="Expediente"),
                     alt.Tooltip("etapa:N", title="Etapa"),
                     alt.Tooltip("segundos:Q", title="Segundos", format=".1f")],
        )
        .properties(height=len(ids) * ALTO_FILA)
    )
