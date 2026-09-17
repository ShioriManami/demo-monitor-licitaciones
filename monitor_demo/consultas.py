"""Consultas cacheadas con `st.cache_data`.

El dataset se lee y valida una sola vez por proceso; las tablas derivadas
(panorama, gráficas, Markdown) también se calculan una vez y se reutilizan en
cada rerun y en cada sesión.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from monitor_demo.datos import Dataset, validar_dataset
from monitor_demo.markdown import ficha_a_markdown

ETIQUETAS_ETAPA = {
    "descarga": "Descarga (simulada)",
    "clasificacion": "Clasificación texto/escaneado",
    "ocr": "OCR selectivo",
    "extraccion": "Extracción de texto",
    "ficha": "Ficha técnica",
}
VEREDICTOS = {True: "Factible", False: "No factible", None: "Indeterminado"}


@st.cache_data(show_spinner="Validando el dataset simulado…")
def dataset() -> Dataset:
    return validar_dataset()


@st.cache_data(show_spinner=False)
def tabla_expedientes() -> pd.DataFrame:
    ds = dataset()
    filas = [
        {
            "id": e.id,
            "siglas": e.siglas,
            "dependencia": e.dependencia,
            "entidad": e.entidad_federativa,
            "estatus": e.estatus,
            "apertura": pd.Timestamp(e.fecha_apertura),
            "guardias": e.numero_guardias,
            "monto_maximo": int(e.monto_maximo),
            "documentos": len(e.documentos),
            "escaneados": e.total_escaneados,
            "evaluacion": VEREDICTOS[ds.fichas[e.id].evaluacion.cumplimos_requisitos],
        }
        for e in ds.expedientes
    ]
    return pd.DataFrame(filas)


@st.cache_data(show_spinner=False)
def datos_graficas() -> dict[str, pd.DataFrame]:
    ds = dataset()
    docs = pd.DataFrame(
        [
            {"expediente": e.id, "tipo": d.tipo, "clasificacion": "Escaneado" if d.escaneado else "Texto",
             "paginas": d.paginas}
            for e in ds.expedientes
            for d in e.documentos
        ]
    )
    por_expediente = (
        docs.groupby(["expediente", "clasificacion"]).size().rename("documentos").reset_index()
    )
    por_tipo = docs.groupby(["tipo", "clasificacion"]).size().rename("documentos").reset_index()
    tiempos = pd.DataFrame(
        [
            {"expediente": e.id, "etapa": ETIQUETAS_ETAPA[etapa], "orden": i, "segundos": round(seg, 1)}
            for e in ds.expedientes
            for i, (etapa, seg) in enumerate(e.tiempos_por_etapa().items())
        ]
    )
    return {"docs": docs, "por_expediente": por_expediente, "por_tipo": por_tipo, "tiempos": tiempos}


@st.cache_data(show_spinner=False)
def markdown_ficha(id_expediente: str) -> str:
    return ficha_a_markdown(dataset().fichas[id_expediente])
