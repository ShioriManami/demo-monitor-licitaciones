"""Vista 3: simulación animada del pipeline sobre los datos locales.

Solo corre al pulsar el botón: sin autoplay, sin hilos ni bucles en segundo
plano. Las pausas usan los tiempos simulados del dataset, comprimidos para que
la animación dure unos segundos.
"""
from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from monitor_demo import ui
from monitor_demo.datos import Dataset, ExpedienteDemo

ETAPAS = [
    ("busqueda", "Búsqueda", ":material/search:", "Convocatorias vigentes de la partida."),
    ("descarga", "Descarga", ":material/download:", "Anexos de cada expediente."),
    ("clasificacion", "Clasificación", ":material/rule:", "¿PDF con texto o escaneado?"),
    ("ocr", "OCR selectivo", ":material/document_scanner:", "Solo en los escaneados."),
    ("extraccion", "Extracción", ":material/article:", "Texto plano por documento."),
    ("ficha", "Ficha técnica", ":material/fact_check:", "Resumen técnico, legal y económico."),
]
VELOCIDADES = {"rapida": ("Rápida · ~8 s", 8.0), "normal": ("Pausada · ~20 s", 20.0)}
PAUSA_MINIMA = 0.02
PAUSA_MAXIMA = 1.2


def render(ds: Dataset) -> None:
    st.subheader("Simular corrida del pipeline", anchor=False)
    st.info(
        "Esto es una **simulación**: recorre el dataset local con temporizadores para mostrar las etapas del "
        "sistema real. No descarga archivos, no ejecuta OCR y no llama a modelos de IA.",
        icon=":material/science:",
    )

    with st.container(horizontal=True, gap="small", key="etapas"):
        for i, (clave, titulo, icono, descripcion) in enumerate(ETAPAS, 1):
            with st.container(border=True, key=f"etapa-{clave}", gap=None):
                st.markdown(f"{icono} **{i}. {titulo}**  \n:gray[{descripcion}]")

    etiquetas = {"todos": f"Todos los expedientes ({len(ds.expedientes)})"}
    etiquetas |= {e.id: f"{e.id} · {e.siglas} · {e.entidad_federativa}" for e in ds.expedientes}
    with st.container(border=True):
        c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
        alcance = c1.selectbox("Alcance", list(etiquetas), format_func=etiquetas.__getitem__, key="sim-alcance")
        velocidad = c2.segmented_control(
            "Velocidad", list(VELOCIDADES), format_func=lambda k: VELOCIDADES[k][0],
            default="rapida", required=True, key="sim-velocidad",
        )
        iniciar = st.button("Simular corrida", type="primary", icon=":material/play_arrow:", key="sim-iniciar")

    if iniciar:
        objetivo = [e for e in ds.expedientes if alcance in ("todos", e.id)]
        st.session_state["sim-resultado"] = _simular(ds, objetivo, VELOCIDADES[velocidad or "rapida"][1])
    elif st.session_state.get("sim-resultado"):
        st.caption("Resultado de la última simulación de esta sesión.")

    if resultado := st.session_state.get("sim-resultado"):
        _resumen(resultado)


def _pausa(segundos: float) -> None:
    time.sleep(min(max(segundos, PAUSA_MINIMA), PAUSA_MAXIMA))


def _simular(ds: Dataset, expedientes: list[ExpedienteDemo], duracion_objetivo: float) -> dict:
    total_simulado = sum(sum(e.tiempos_por_etapa().values()) for e in expedientes)
    escala = duracion_objetivo / total_simulado
    pasos = 1 + sum(len(e.documentos) + 1 for e in expedientes)
    hechos = 0
    filas = []
    inicio = time.perf_counter()

    with st.status("Simulación en curso…", expanded=True) as status:
        barra = st.progress(0.0, text="Etapa 1 · Búsqueda de convocatorias")
        actual = st.empty()
        actual.markdown(":material/search: Buscando convocatorias vigentes · simulado: se lee el dataset local")
        _pausa(0.6)
        hechos += 1
        barra.progress(hechos / pasos, text="Etapa 1 · Búsqueda de convocatorias")
        st.markdown(f":material/check: **{len(expedientes)}** expediente(s) encontrados en `demo_data/`")

        for e in expedientes:
            for doc in e.documentos:
                if doc.escaneado:
                    etapa = "Etapa 4 · OCR selectivo"
                    detalle = (f":material/document_scanner: OCR simulado en `{doc.nombre}` "
                               f"({doc.paginas} págs · {doc.chars_por_pagina} car./pág → escaneado)")
                else:
                    etapa = "Etapa 5 · Extracción de texto"
                    detalle = f":material/article: Extracción directa de `{doc.nombre}` ({doc.paginas} págs · con texto)"
                actual.markdown(f"**{e.id}** · :material/download: descarga → :material/rule: clasificación → {detalle}")
                _pausa(doc.tiempos.total * escala)
                hechos += 1
                barra.progress(hechos / pasos, text=f"{etapa} · {e.id} · {hechos}/{pasos}")

            actual.markdown(f"**{e.id}** · :material/fact_check: Cargando la ficha de ejemplo precalculada")
            _pausa(e.tiempo_ficha_seg * escala)
            hechos += 1
            barra.progress(hechos / pasos, text=f"Etapa 6 · Ficha técnica · {e.id} · {hechos}/{pasos}")

            etiqueta, _, icono = ui.veredicto(ds.fichas[e.id])
            tiempos = e.tiempos_por_etapa()
            st.markdown(
                f"{icono} **{e.id}** · {len(e.documentos)} docs ({e.total_escaneados} con OCR) · "
                f"{sum(tiempos.values()):.0f} s simulados · {etiqueta}"
            )
            filas.append({
                "Expediente": e.id,
                "Docs": len(e.documentos),
                "Con OCR": e.total_escaneados,
                "Descarga (s)": round(tiempos["descarga"], 1),
                "Clasificación (s)": round(tiempos["clasificacion"], 1),
                "OCR (s)": round(tiempos["ocr"], 1),
                "Extracción (s)": round(tiempos["extraccion"], 1),
                "Ficha (s)": round(tiempos["ficha"], 1),
                "Total (s)": round(sum(tiempos.values()), 1),
                "Evaluación": etiqueta,
            })

        actual.empty()
        duracion_real = time.perf_counter() - inicio
        barra.progress(1.0, text="Simulación completada")
        status.update(
            label=f"Simulación completada · {len(expedientes)} expediente(s) en {duracion_real:.1f} s reales",
            state="complete",
            expanded=False,
        )

    return {
        "filas": filas,
        "duracion_real": duracion_real,
        "total_simulado": total_simulado,
        "documentos": sum(len(e.documentos) for e in expedientes),
        "ocr": sum(e.total_escaneados for e in expedientes),
    }


def _resumen(resultado: dict) -> None:
    st.markdown("##### Resumen de la simulación")
    with st.container(horizontal=True, gap="small", key="metricas-simulacion"):
        st.metric("Expedientes", len(resultado["filas"]), border=True)
        st.metric("Documentos", resultado["documentos"], border=True)
        st.metric("Pasaron por OCR", resultado["ocr"], border=True)
        st.metric("Tiempo simulado", f"{resultado['total_simulado'] / 60:.1f} min", border=True,
                  help="Suma de los tiempos por etapa definidos en el dataset simulado")
        st.metric("Duración de la animación", f"{resultado['duracion_real']:.1f} s", border=True)
    st.dataframe(pd.DataFrame(resultado["filas"]), hide_index=True, height=(len(resultado["filas"]) + 1) * 35 + 3)
    st.caption(
        "Los tiempos por etapa son valores simulados del dataset; la animación los comprime "
        f"≈{resultado['total_simulado'] / max(resultado['duracion_real'], 0.1):.0f}×."
    )
