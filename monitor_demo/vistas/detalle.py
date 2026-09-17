"""Vista 2: detalle de UN expediente (documentos, texto extraído y ficha técnica).

Solo se construye el expediente seleccionado, y dentro de la ficha solo la
pestaña abierta (`st.tabs(on_change="rerun")` + `.open`).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from monitor_demo import consultas, ui
from monitor_demo.datos import UMBRAL_CHARS_POR_PAGINA, Dataset, ExpedienteDemo
from monitor_demo.esquemas import FichaTecnica
from monitor_demo.markdown import AVISO_FICHA, ficha_a_markdown

ETIQUETA_PUNTO = {"riesgo": "Riesgo", "oportunidad": "Oportunidad", "observacion": "Observación"}


def render(ds: Dataset) -> None:
    ids = [e.id for e in ds.expedientes]
    etiquetas = {e.id: f"{e.id} · {e.siglas} · {e.entidad_federativa}" for e in ds.expedientes}
    if "id" not in st.session_state:
        pedido = st.query_params.get("id")
        st.session_state["id"] = pedido if pedido in ids else ids[0]
    id_sel = st.selectbox(
        "Expediente", ids, format_func=etiquetas.__getitem__, key="id", persist_state="session",
    )
    if st.query_params.get("id") != id_sel:
        st.query_params["id"] = id_sel
    exp = ds.expediente(id_sel)
    ficha = ds.fichas[id_sel]

    _encabezado(exp, ficha)
    st.space("small")
    _documentos(exp, ds.textos[exp.id])
    st.divider()
    _ficha(exp, ficha)


def _encabezado(exp: ExpedienteDemo, ficha: FichaTecnica) -> None:
    st.subheader(exp.nombre_procedimiento, anchor=False)
    etiqueta, color, icono = ui.veredicto(ficha)
    with st.container(horizontal=True, gap="small"):
        st.badge(exp.id, icon=":material/tag:", color="gray")
        st.badge(exp.estatus, icon=":material/schedule:", color="blue")
        st.badge(exp.tipo_procedimiento, icon=":material/gavel:", color="violet")
        st.badge(etiqueta, icon=icono, color=color)
    st.caption(f"{exp.dependencia} · {exp.unidad_compradora} · {exp.entidad_federativa}")

    guardias = f"{exp.numero_guardias}"
    if exp.numero_guardias_maximo:
        guardias += f"–{exp.numero_guardias_maximo}"
    with st.container(horizontal=True, gap="small", key="metricas-detalle"):
        st.metric("Documentos", f"{len(exp.documentos)} · {exp.total_escaneados} esc.", border=True)
        st.metric("Páginas", exp.total_paginas, border=True)
        st.metric("Guardias", guardias, border=True)
        st.metric("Monto máximo", ui.mxn_compacto(exp.monto_maximo), border=True)
        st.metric("Apertura", ui.fecha(exp.fecha_apertura), border=True)


def _documentos(exp: ExpedienteDemo, textos: dict[str, str]) -> None:
    izquierda, derecha = st.columns([1, 1.45], gap="medium")
    with izquierda:
        st.markdown("##### Documentos del expediente")
        for i, doc in enumerate(exp.documentos):
            with st.container(border=True, horizontal=True, vertical_alignment="center", gap="small",
                              wrap=False, key=f"doc-{i}"):
                st.markdown(
                    f"**{doc.nombre}**  \n:gray[{doc.tipo} · {doc.paginas} págs · {doc.tamano_kb:,} KB]",
                    width="stretch",
                )
                ui.badge_clasificacion(doc)
    with derecha:
        st.markdown("##### Texto extraído")
        nombres = [d.nombre for d in exp.documentos]
        nombre = st.selectbox("Documento", nombres, key=f"texto-{exp.id}", label_visibility="collapsed")
        doc = next(d for d in exp.documentos if d.nombre == nombre)
        if doc.escaneado:
            criterio = (f"{doc.chars_por_pagina} caracteres/página (< {UMBRAL_CHARS_POR_PAGINA}) → "
                        "escaneado: el texto se obtuvo con OCR simulado")
        else:
            criterio = (f"{doc.chars_por_pagina:,} caracteres/página → texto nativo: extracción directa, sin OCR"
                        if doc.formato == "pdf" else "Documento Word → extracción directa de párrafos y tablas")
        with st.container(horizontal=True, gap="small", vertical_alignment="center"):
            ui.badge_clasificacion(doc)
            st.caption(criterio, width="content")
        st.code(textos[nombre], language=None, wrap_lines=True, height=380)
        st.caption("Fragmento sintético escrito para la demo: no proviene de ningún documento real.")


def _ficha(exp: ExpedienteDemo, ficha: FichaTecnica) -> None:
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.subheader("Ficha técnica", anchor=False, width="content")
        st.badge(AVISO_FICHA, icon=":material/inventory_2:", color="violet")
        st.space("stretch")
        st.download_button(
            "Descargar ficha (.md)",
            data=lambda: ficha_a_markdown(ficha),
            file_name=f"ficha_{exp.id}.md",
            mime="text/markdown",
            icon=":material/download:",
            on_click="ignore",
            key="descargar-md",
        )

    ev = ficha.evaluacion
    etiqueta, _, icono = ui.veredicto(ficha)
    titulo = f"{etiqueta} · confianza {ev.confianza_evaluacion}"
    if ev.cumplimos_requisitos is True:
        st.success(ev.razonamiento, title=titulo, icon=icono)
    elif ev.cumplimos_requisitos is False:
        st.error(ev.razonamiento, title=titulo, icon=icono)
    else:
        st.warning(ev.razonamiento, title=titulo, icon=icono)
    if ev.partidas_no_vigilancia_detectadas:
        st.info("Expediente mixto: " + ", ".join(ev.partidas_no_vigilancia_detectadas), icon=":material/call_split:")
    for aviso in ficha.errores_extraccion:
        st.warning(aviso, icon=":material/warning:")

    if ev.puntos_criticos:
        st.markdown(f"##### Puntos críticos ({len(ev.puntos_criticos)})")
        for i, p in enumerate(ev.puntos_criticos):
            with st.container(key=f"punto-{p.tipo}-{i}", gap=None):
                st.markdown(f"**{ETIQUETA_PUNTO[p.tipo]} · {p.severidad}** — {p.descripcion}")
                if p.cita_literal:
                    st.caption(f"«{p.cita_literal}» — {', '.join(p.fuentes)}")

    tecnica, legal, economica = st.tabs(
        [":material/engineering: Técnica", ":material/balance: Legal", ":material/payments: Económica"],
        key="ficha-tab",
        on_change="rerun",
    )
    if tecnica.open:
        with tecnica:
            _tab_tecnica(ficha)
    if legal.open:
        with legal:
            _tab_legal(ficha)
    if economica.open:
        with economica:
            _tab_economica(ficha)

    citas = st.expander(f"Citas clave verificables ({len(ficha.citas_clave)})", icon=":material/format_quote:",
                        key="citas", on_change="rerun")
    if citas.open:
        with citas:
            for c in ficha.citas_clave:
                st.markdown(f"**`{c.campo}`** = `{c.valor}` · :gray[{c.fuente}]  \n> {c.cita_literal}")
    vista_md = st.expander("Vista previa del Markdown", icon=":material/description:", key="vista-md",
                           on_change="rerun")
    if vista_md.open:
        with vista_md:
            st.code(consultas.markdown_ficha(exp.id), language="markdown", height=420)
    st.caption(f"Origen: {ficha.modelo_usado} · generada {ui.fecha_hora(ficha.timestamp_generacion)}")


def _tabla(filas: list[tuple[str, str]]) -> None:
    cuerpo = "\n".join(f"| {k} | {v} |" for k, v in filas)
    st.markdown(f"| Concepto | Valor |\n|---|---|\n{cuerpo}")


def _lista(titulo: str, items: list[str]) -> None:
    if items:
        st.markdown(f"**{titulo}**\n" + "\n".join(f"- {x}" for x in items))


def _tab_tecnica(ficha: FichaTecnica) -> None:
    t, p = ficha.tecnicos, ficha.tecnicos.perfil_personal
    elementos = f"{t.numero_total_elementos}"
    if t.numero_total_elementos_maximo:
        elementos += f"–{t.numero_total_elementos_maximo}"
    with st.container(horizontal=True, gap="small", key="metricas-tecnica"):
        st.metric("Elementos (mín–máx)", elementos)
        st.metric("Armados / sin arma", f"{p.cantidad_guardias_armados or 0} / {p.cantidad_guardias_desarmados or 0}")
        st.metric("Inmuebles", len(t.distribucion_inmuebles))
        st.metric("Experiencia mínima", ui.o(t.experiencia_minima_anios, " años"))
    st.markdown(f"**Servicio:** {t.servicio_solicitado}  \n**Horario:** {ui.o(t.horarios_cobertura)}")

    st.dataframe(
        pd.DataFrame([d.model_dump() for d in t.distribucion_inmuebles]).fillna("—"),
        hide_index=True,
        column_config={
            "inmueble": st.column_config.TextColumn("Inmueble", width="large"),
            "cantidad_elementos": st.column_config.NumberColumn("Elementos", format="%d"),
            "turno": "Turno",
            "notas": "Notas",
        },
    )

    a = t.alcance_servicio
    izq, der = st.columns(2, gap="medium")
    with izq:
        st.markdown("**Perfil y operación**")
        _tabla([
            ("Edad", f"{ui.o(p.edad_minima)} a {ui.o(p.edad_maxima)} años"),
            ("Escolaridad mínima", ui.o(p.escolaridad_minima)),
            ("Cobertura de faltas", ui.o(t.tiempo_cobertura_faltas_minutos, " min")),
            ("Tolerancia de retardo", ui.o(t.tolerancia_retardo_minutos, " min")),
            ("Rondines por turno", ui.o(t.rondines_minimo_por_turno)),
            ("Permite doblar turno", ui.si_no(t.permite_doblete_turno)),
            ("Examen médico", ui.o(t.examen_medico_frecuencia)),
            ("Psicométrico / toxicológico", f"{ui.si_no(t.requiere_examen_psicometrico)} / {ui.si_no(t.requiere_examen_toxicologico)}"),
        ])
    with der:
        st.markdown("**Alcance, permisos e infraestructura**")
        _tabla([
            ("Intramuros / extramuros", f"{ui.si_no(a.vigilancia_intramuros)} / {ui.si_no(a.vigilancia_extramuros)}"),
            ("CCTV / alarmas", f"{ui.si_no(a.incluye_cctv)} / {ui.si_no(a.incluye_alarmas)}"),
            ("Arcos detectores", ui.si_no(a.incluye_arcos_metales)),
            ("Inventario mínimo de armas", ui.o(t.inventario_armas_minimo)),
            ("Entidades mínimas en permiso", ui.o(t.entidades_federativas_permiso_minimas)),
            ("Oficina local", ui.si_no(t.requiere_oficina_local) + (f" ({t.entidad_oficina_requerida})" if t.entidad_oficina_requerida else "")),
            ("Línea telefónica exclusiva", ui.si_no(t.requiere_linea_telefonica_exclusiva)),
        ])
    izq, der = st.columns(2, gap="medium")
    with izq:
        _lista("Equipamiento exigido", t.equipamiento_exigido)
        _lista("Protocolos sectoriales", t.codigos_sectoriales)
        _lista("Otros componentes del alcance", a.otros)
    with der:
        cap = t.capacitacion
        _lista("Capacitación (DC-3)", [*cap.cursos_dc3,
                                        f"{ui.num(cap.porcentaje_dc3_inicial, '%')} del personal con DC-3 al proponer; "
                                        f"100% en {ui.o(cap.plazo_dc3_completo_dias)} días hábiles"])
        _lista("Requisitos adicionales del personal", p.requisitos_adicionales)


def _tab_legal(ficha: FichaTecnica) -> None:
    leg = ficha.legales
    with st.container(horizontal=True, gap="small", key="metricas-legal"):
        st.metric("Garantía de cumplimiento", ui.num(leg.garantia_cumplimiento_pct, "%"))
        st.metric("Visita obligatoria", ui.si_no(leg.requiere_visita_obligatoria))
        st.metric("Permite MIPYMES", ui.si_no(leg.permite_mipymes))
        st.metric("Participación conjunta", ui.si_no(leg.permite_participacion_conjunta))

    izq, der = st.columns(2, gap="medium")
    with izq:
        st.markdown("**Calendario**")
        filas = [("Junta de aclaraciones", ui.fecha_hora(leg.fecha_junta_aclaraciones))]
        if leg.fecha_visita_obligatoria:
            filas.append(("Visita obligatoria", ui.fecha_hora(leg.fecha_visita_obligatoria)))
        filas += [
            ("Apertura de proposiciones", ui.fecha_hora(leg.fecha_apertura)),
            ("Fallo", ui.fecha_hora(leg.fecha_fallo)),
            ("Firma de contrato", ui.fecha_hora(leg.fecha_firma_contrato)),
        ]
        _tabla(filas)
    with der:
        st.markdown("**Marco del contrato**")
        _tabla([
            ("Plazo", ui.o(leg.plazo_contrato)),
            ("Entrega de garantía", ui.o(leg.dias_entrega_garantia_tras_firma, " días naturales tras la firma")),
            ("Ley aplicable", ui.o(leg.ley_aplicable)),
            ("Plataforma", ui.o(leg.plataforma_electronica)),
        ])
    izq, der = st.columns(2, gap="medium")
    with izq:
        _lista("Documentos obligatorios", leg.documentos_obligatorios)
    with der:
        _lista("Requisitos legales detectados", leg.requisitos_legales_listado)


def _tab_economica(ficha: FichaTecnica) -> None:
    eco = ficha.economicos
    with st.container(horizontal=True, gap="small", key="metricas-economica"):
        st.metric("Monto mínimo", ui.mxn(eco.monto_minimo))
        st.metric("Monto máximo", ui.mxn(eco.monto_maximo))
        st.metric("Presupuesto autorizado", ui.mxn(eco.presupuesto_autorizado))
        st.metric("Pena convencional", ui.num(eco.pena_convencional_pct_dia, "% / día"))

    izq, der = st.columns(2, gap="medium")
    with izq:
        st.markdown("**Condiciones**")
        _tabla([
            ("Tipo de contrato", ui.o(eco.tipo_contrato)),
            ("Plurianual", ui.si_no(eco.es_plurianual)),
            ("Anticipo", ui.si_no(eco.anticipo)),
            ("Forma de pago", ui.o(eco.forma_pago)),
            ("Moneda", eco.moneda),
        ])
    with der:
        st.markdown("**Exposición financiera**")
        _tabla([
            ("Póliza de responsabilidad civil", ui.num(eco.poliza_responsabilidad_civil_pct, "% del monto máximo")),
            ("Pago de deducible por robo", ui.o(eco.dias_pago_deducible_robo, " días hábiles")),
            ("Pena convencional", ui.num(eco.pena_convencional_pct_dia, "% por día natural")),
        ])
    izq, der = st.columns(2, gap="medium")
    with izq:
        _lista("Deductivas", eco.deductivas_descripcion)
    with der:
        _lista("Requisitos económicos detectados", eco.requisitos_economicos_listado)
