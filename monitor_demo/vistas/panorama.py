"""Vista 1: panorama con filtros y métricas."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from monitor_demo import consultas, ui
from monitor_demo.datos import Dataset


def render(ds: Dataset) -> None:
    df = consultas.tabla_expedientes()

    st.subheader("Panorama de expedientes", anchor=False)
    st.caption(
        f"{len(df)} expedientes simulados de servicios de vigilancia · corte al {ui.fecha(ds.fecha_corte)}. "
        "Seleccioná una fila para abrir su detalle."
    )

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1, 1.35, 1, 1.1])
        entidades = c1.multiselect(
            "Entidad federativa", sorted(df["entidad"].unique()), placeholder="Todas",
            key="f_entidad", persist_state="session",
        )
        dependencias = c2.multiselect(
            "Dependencia", sorted(df["dependencia"].unique()), placeholder="Todas",
            key="f_dependencia", persist_state="session",
        )
        inicio, fin = df["apertura"].min().date(), df["apertura"].max().date()
        rango = c3.date_input(
            "Apertura de proposiciones", value=(inicio, fin), min_value=inicio, max_value=fin,
            format="DD/MM/YYYY", key="f_fechas", persist_state="session",
        )
        tope = float(math.ceil(df["monto_maximo"].max() / 1_000_000))
        montos = c4.slider(
            "Monto máximo (millones MXN)", 0.0, tope, (0.0, tope), step=0.5, format="$%.1f M",
            key="f_montos", persist_state="session",
        )

    mascara = pd.Series(True, index=df.index)
    if entidades:
        mascara &= df["entidad"].isin(entidades)
    if dependencias:
        mascara &= df["dependencia"].isin(dependencias)
    if isinstance(rango, tuple) and len(rango) == 2:
        mascara &= df["apertura"].dt.date.between(rango[0], rango[1])
    mascara &= df["monto_maximo"].between(montos[0] * 1_000_000, montos[1] * 1_000_000)
    filtrados = df[mascara]

    total_docs = int(filtrados["documentos"].sum())
    escaneados = int(filtrados["escaneados"].sum())
    with st.container(horizontal=True, gap="small", key="metricas-panorama"):
        st.metric("Expedientes", f"{len(filtrados)} de {len(df)}", border=True)
        st.metric(
            "Documentos", total_docs, border=True,
            help="Anexos simulados por expediente (convocatoria, anexo técnico, contrato, actas…)",
        )
        st.metric(
            "Escaneados (OCR)", f"{escaneados} · {escaneados / total_docs:.0%}" if total_docs else "0",
            border=True, help="PDFs sin capa de texto: son los únicos que pasan por OCR",
        )
        st.metric("Guardias requeridos", f"{int(filtrados['guardias'].sum()):,}", border=True,
                  help="Suma del mínimo de elementos exigido por cada expediente")
        st.metric("Monto máximo total", ui.mxn_compacto(float(filtrados["monto_maximo"].sum())), border=True)

    if filtrados.empty:
        st.info("Ningún expediente coincide con los filtros.", icon=":material/filter_alt_off:")
        return

    factibles = int((filtrados["evaluacion"] == "Factible").sum())
    no_factibles = int((filtrados["evaluacion"] == "No factible").sum())
    indeterminados = len(filtrados) - factibles - no_factibles
    st.caption("Evaluación de las fichas de ejemplo precalculadas:")
    with st.container(horizontal=True, gap="small", key="resumen-evaluacion"):
        st.badge(ui.plural(factibles, "factible", "factibles"), icon=":material/check_circle:", color="green")
        st.badge(ui.plural(no_factibles, "no factible", "no factibles"), icon=":material/cancel:", color="red")
        st.badge(ui.plural(indeterminados, "indeterminado", "indeterminados"), icon=":material/help:",
                 color="orange")

    evento = st.dataframe(
        filtrados,
        hide_index=True,
        height=(len(filtrados) + 1) * 35 + 3,
        on_select="rerun",
        selection_mode="single-row",
        key="tabla_panorama",
        column_order=["id", "siglas", "entidad", "estatus", "apertura", "guardias", "monto_maximo",
                      "documentos", "escaneados", "evaluacion"],
        column_config={
            "id": st.column_config.TextColumn("Expediente", pinned=True),
            "siglas": st.column_config.TextColumn("Dependencia", help="Siglas de la dependencia ficticia"),
            "entidad": "Entidad",
            "estatus": "Estatus",
            "apertura": st.column_config.DatetimeColumn("Apertura", format="DD/MM/YYYY"),
            "guardias": st.column_config.NumberColumn("Guardias", format="%d"),
            "monto_maximo": st.column_config.NumberColumn("Monto máx. (MXN)", format="$%,d"),
            "documentos": st.column_config.NumberColumn("Docs", format="%d"),
            "escaneados": st.column_config.NumberColumn("Escaneados", format="%d"),
            "evaluacion": "Evaluación",
        },
    )

    filas = evento.selection.rows if evento else []
    if filas:
        fila = filtrados.iloc[filas[0]]
        with st.container(border=True, horizontal=True, vertical_alignment="center", key="seleccion"):
            st.markdown(
                f"**{fila['id']}** · {fila['dependencia']} · {fila['entidad']}  \n"
                f"{ds.expediente(fila['id']).nombre_procedimiento}",
                width="stretch",
            )
            st.button(
                "Abrir detalle", icon=":material/arrow_forward:", type="primary",
                on_click=ui.ir_a_detalle, args=(fila["id"],),
            )
