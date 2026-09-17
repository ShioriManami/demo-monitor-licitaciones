"""Convierte una FichaTecnica en un reporte Markdown, generado localmente."""
from __future__ import annotations

from datetime import datetime

from monitor_demo.esquemas import FichaTecnica

AVISO_FICHA = "Ficha de ejemplo precalculada para la demo"

VEREDICTOS = {True: "Factible", False: "No factible", None: "Indeterminado"}
TIPOS_PUNTO = {"riesgo": "Riesgo", "oportunidad": "Oportunidad", "observacion": "Observación"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _o(valor: object) -> str:
    if valor is None or valor == "" or valor == []:
        return "—"
    return str(valor)


def _si_no(valor: bool | None) -> str:
    return {True: "Sí", False: "No", None: "—"}[valor]


def _monto(valor: float | None, moneda: str = "MXN") -> str:
    return "—" if valor is None else f"${valor:,.2f} {moneda}"


def _pct(valor: float | None) -> str:
    return "—" if valor is None else f"{valor:g}%"


def _fecha(valor: datetime | None) -> str:
    if valor is None:
        return "—"
    return f"{valor.day} {MESES[valor.month - 1]} {valor.year}, {valor:%H:%M}"


def _tabla(filas: list[tuple[str, str]], encabezado: tuple[str, str] = ("Campo", "Valor")) -> list[str]:
    salida = [f"| {encabezado[0]} | {encabezado[1]} |", "|---|---|"]
    salida += [f"| {campo} | {valor.replace('|', '/')} |" for campo, valor in filas]
    return [*salida, ""]


def _lista(titulo: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"### {titulo}", "", *[f"- {item}" for item in items], ""]


def ficha_a_markdown(ficha: FichaTecnica) -> str:
    ident, ev = ficha.identificacion, ficha.evaluacion
    tec, leg, eco = ficha.tecnicos, ficha.legales, ficha.economicos
    perfil, alcance, cap = tec.perfil_personal, tec.alcance_servicio, tec.capacitacion

    md: list[str] = [
        f"# {ident.numero_procedimiento} · {ident.nombre_procedimiento}",
        "",
        f"> **{AVISO_FICHA}.** Todos los datos son sintéticos: no corresponden a una convocatoria real "
        "ni se generaron con un modelo de IA en vivo.",
        "",
        f"{ident.dependencia} · {_o(ident.entidad_federativa)} · {_o(ident.tipo_procedimiento)}",
        "",
        "## Veredicto",
        "",
        f"**{VEREDICTOS[ev.cumplimos_requisitos]}** · confianza {ev.confianza_evaluacion}",
        "",
    ]
    if ev.razonamiento:
        md += [f"> {ev.razonamiento}", ""]
    if ev.partidas_no_vigilancia_detectadas:
        md += _lista("Expediente mixto: partidas ajenas a vigilancia", ev.partidas_no_vigilancia_detectadas)
    if ev.puntos_criticos:
        md += [f"### Puntos críticos ({len(ev.puntos_criticos)})", ""]
        for p in ev.puntos_criticos:
            md.append(f"- **[{p.severidad.upper()}] {TIPOS_PUNTO[p.tipo]}:** {p.descripcion}")
            if p.fuentes:
                md.append(f"  - Fuente: {', '.join(f'`{f}`' for f in p.fuentes)}")
            if p.cita_literal:
                md.append(f"  - Cita: «{p.cita_literal}»")
        md.append("")

    md += ["## Identificación", ""]
    md += _tabla([
        ("Número de procedimiento", f"`{ident.numero_procedimiento}`"),
        ("Código de expediente", f"`{_o(ident.codigo_expediente)}`"),
        ("Dependencia", ident.dependencia),
        ("Unidad compradora", _o(ident.unidad_compradora)),
        ("Entidad federativa", _o(ident.entidad_federativa)),
        ("Tipo / carácter", f"{_o(ident.tipo_procedimiento)} / {_o(ident.caracter)}"),
        ("Partidas", ", ".join(ident.partidas) or "—"),
        ("Objeto", _o(ident.objeto_contrato)),
    ])

    elementos = _o(tec.numero_total_elementos)
    if tec.numero_total_elementos_maximo:
        elementos = f"{tec.numero_total_elementos} (mín.) / {tec.numero_total_elementos_maximo} (máx.)"
    md += ["## Aspectos técnicos", "", f"**Servicio solicitado:** {_o(tec.servicio_solicitado)}", ""]
    md += _tabla([
        ("Total de elementos", elementos),
        ("Guardias armados / sin arma", f"{_o(perfil.cantidad_guardias_armados)} / {_o(perfil.cantidad_guardias_desarmados)}"),
        ("Horario de cobertura", _o(tec.horarios_cobertura)),
        ("Edad", f"{_o(perfil.edad_minima)} a {_o(perfil.edad_maxima)} años"),
        ("Escolaridad mínima", _o(perfil.escolaridad_minima)),
        ("Experiencia mínima", f"{tec.experiencia_minima_anios} años" if tec.experiencia_minima_anios else "—"),
        ("Cobertura de faltas", f"{tec.tiempo_cobertura_faltas_minutos} min" if tec.tiempo_cobertura_faltas_minutos else "—"),
        ("Tolerancia de retardo", f"{tec.tolerancia_retardo_minutos} min" if tec.tolerancia_retardo_minutos else "—"),
        ("Rondines por turno", _o(tec.rondines_minimo_por_turno)),
        ("Permite doblar turno", _si_no(tec.permite_doblete_turno)),
        ("Inventario mínimo de armas", _o(tec.inventario_armas_minimo)),
        ("Entidades mínimas en permiso", _o(tec.entidades_federativas_permiso_minimas)),
        ("Oficina local", f"{_si_no(tec.requiere_oficina_local)} {f'({tec.entidad_oficina_requerida})' if tec.entidad_oficina_requerida else ''}".strip()),
    ])
    if tec.distribucion_inmuebles:
        md += ["### Distribución por inmueble", "", "| Inmueble | Elementos | Turno | Notas |", "|---|---:|---|---|"]
        md += [f"| {d.inmueble} | {d.cantidad_elementos} | {_o(d.turno)} | {_o(d.notas)} |" for d in tec.distribucion_inmuebles]
        md.append("")
    md += ["### Alcance del servicio", ""]
    md += _tabla([
        ("Vigilancia intramuros", _si_no(alcance.vigilancia_intramuros)),
        ("Vigilancia extramuros", _si_no(alcance.vigilancia_extramuros)),
        ("CCTV", _si_no(alcance.incluye_cctv)),
        ("Alarmas", _si_no(alcance.incluye_alarmas)),
        ("Arcos detectores de metales", _si_no(alcance.incluye_arcos_metales)),
    ], ("Componente", "Incluye"))
    md += _lista("Otros componentes", alcance.otros)
    md += _lista("Equipamiento exigido", tec.equipamiento_exigido)
    md += _lista("Protocolos sectoriales", tec.codigos_sectoriales)
    md += _lista("Requisitos adicionales del personal", perfil.requisitos_adicionales)
    md += _lista("Cursos DC-3", cap.cursos_dc3)

    md += ["## Aspectos legales", ""]
    md += _tabla([
        ("Ley aplicable", _o(leg.ley_aplicable)),
        ("Plazo del contrato", _o(leg.plazo_contrato)),
        ("Garantía de cumplimiento", _pct(leg.garantia_cumplimiento_pct)),
        ("Entrega de garantía", f"{leg.dias_entrega_garantia_tras_firma} días naturales tras la firma" if leg.dias_entrega_garantia_tras_firma else "—"),
        ("Permite MIPYMES", _si_no(leg.permite_mipymes)),
        ("Participación conjunta", _si_no(leg.permite_participacion_conjunta)),
        ("Visita obligatoria", _si_no(leg.requiere_visita_obligatoria)),
        ("Plataforma", _o(leg.plataforma_electronica)),
    ])
    md += ["### Calendario", ""]
    calendario = [
        ("Junta de aclaraciones", _fecha(leg.fecha_junta_aclaraciones)),
        ("Apertura de proposiciones", _fecha(leg.fecha_apertura)),
        ("Fallo", _fecha(leg.fecha_fallo)),
        ("Firma de contrato", _fecha(leg.fecha_firma_contrato)),
    ]
    if leg.fecha_visita_obligatoria:
        calendario.insert(1, ("Visita obligatoria", _fecha(leg.fecha_visita_obligatoria)))
    md += _tabla(calendario, ("Evento", "Fecha"))
    md += _lista("Documentos obligatorios", leg.documentos_obligatorios)

    md += ["## Aspectos económicos", ""]
    md += _tabla([
        ("Monto mínimo", _monto(eco.monto_minimo, eco.moneda)),
        ("Monto máximo", _monto(eco.monto_maximo, eco.moneda)),
        ("Presupuesto autorizado", _monto(eco.presupuesto_autorizado, eco.moneda)),
        ("Tipo de contrato", _o(eco.tipo_contrato)),
        ("Plurianual", _si_no(eco.es_plurianual)),
        ("Anticipo", _si_no(eco.anticipo)),
        ("Forma de pago", _o(eco.forma_pago)),
        ("Pena convencional por día", _pct(eco.pena_convencional_pct_dia)),
        ("Póliza de responsabilidad civil", _pct(eco.poliza_responsabilidad_civil_pct)),
        ("Pago de deducible por robo", f"{eco.dias_pago_deducible_robo} días hábiles" if eco.dias_pago_deducible_robo else "—"),
    ])
    md += _lista("Deductivas", eco.deductivas_descripcion)

    if ficha.citas_clave:
        md += ["## Citas clave", ""]
        for c in ficha.citas_clave:
            md += [f"- **`{c.campo}`** = `{c.valor}` · fuente `{c.fuente}`", f"  > {c.cita_literal}"]
        md.append("")

    md += ["## Metadata", ""]
    md += [f"- Origen: {ficha.modelo_usado}", f"- Generada: {_fecha(ficha.timestamp_generacion)}",
           f"- Archivos procesados ({len(ficha.archivos_procesados)}): "
           + ", ".join(f"`{a}`" for a in ficha.archivos_procesados)]
    md += [f"- Aviso de extracción: {err}" for err in ficha.errores_extraccion]
    md += ["", "---", "", "Diseño y desarrollo: [Alan Mendoza](https://portafolio-ki87.vercel.app)", ""]
    return "\n".join(md)
