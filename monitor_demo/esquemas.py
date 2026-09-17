"""Modelos Pydantic de la ficha técnica.

Son las mismas definiciones de datos que usa el sistema original para la
ficha técnica consolidada por expediente (solo los modelos: sin prompts,
clientes de IA ni lógica de extracción). Las descripciones se reescribieron
con ejemplos genéricos.

Estructura:
  FichaTecnica
    ├── IdentificacionFicha
    ├── EvaluacionCumplimiento (+ RiesgoOportunidad)
    ├── CitaClave
    ├── AspectosTecnicos
    ├── AspectosLegales
    └── AspectosEconomicos
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# -------- Sub-modelos --------


class IdentificacionFicha(BaseModel):
    """Datos básicos que identifican la convocatoria."""
    model_config = ConfigDict(extra="ignore")

    numero_procedimiento: str
    codigo_expediente: str | None = None
    nombre_procedimiento: str
    objeto_contrato: str | None = Field(
        default=None,
        description="Descripción del objeto del contrato (puede diferir del nombre del procedimiento)",
    )
    dependencia: str
    unidad_compradora: str | None = None
    entidad_federativa: str | None = None
    tipo_procedimiento: str | None = None  # Licitación pública, invitación, adjudicación directa
    caracter: str | None = None  # Nacional, internacional
    partidas: list[str] = Field(
        default_factory=list,
        description="Claves de partida presupuestal; un expediente puede tener varias",
    )


class DistribucionInmueble(BaseModel):
    """Cantidad de elementos asignados a un inmueble específico."""
    model_config = ConfigDict(extra="ignore")

    inmueble: str = Field(..., description="Nombre o dirección del inmueble")
    cantidad_elementos: int = Field(..., description="Número de guardias asignados a este inmueble")
    turno: str | None = Field(default=None, description="Ej. '24x24', '12x12', '8 horas'")
    notas: str | None = None


class PerfilPersonal(BaseModel):
    """Perfil exigido al personal de vigilancia."""
    model_config = ConfigDict(extra="ignore")

    armado: bool | None = Field(default=None, description="True si requiere personal armado")
    cantidad_guardias_armados: int | None = Field(
        default=None, description="Cantidad mínima de guardias armados"
    )
    cantidad_guardias_desarmados: int | None = Field(
        default=None, description="Cantidad mínima de guardias sin arma"
    )
    edad_minima: int | None = None
    edad_maxima: int | None = None
    escolaridad_minima: str | None = Field(
        default=None, description="Ej. 'secundaria', 'preparatoria'"
    )
    requisitos_adicionales: list[str] = Field(
        default_factory=list,
        description="Otros requisitos (ej. 'sin antecedentes penales', 'examen médico vigente')",
    )


class EquipoSupervision(BaseModel):
    """Personal de mando o supervisión exigido (sin costo para la convocante)."""
    model_config = ConfigDict(extra="ignore")

    ejecutivo_cuenta: int | None = Field(default=None, description="Ejecutivos de cuenta requeridos")
    coordinador_operativo: int | None = Field(
        default=None, description="Coordinadores o supervisores operativos generales"
    )
    supervisores_inmuebles: int | None = Field(
        default=None, description="Cantidad mínima de supervisores de inmuebles"
    )
    capacitador_interno_dc5: int | None = Field(
        default=None, description="Capacitadores internos con registro DC-5"
    )
    capacitadores_externos_dc5: int | None = Field(
        default=None, description="Capacitadores externos con registro DC-5"
    )


class AlcanceServicio(BaseModel):
    """Tipos de servicio incluidos."""
    model_config = ConfigDict(extra="ignore")

    vigilancia_intramuros: bool | None = None
    vigilancia_extramuros: bool | None = None
    incluye_cctv: bool | None = None
    incluye_alarmas: bool | None = None
    incluye_arcos_metales: bool | None = None
    otros: list[str] = Field(default_factory=list)


class Capacitacion(BaseModel):
    """Cursos, certificaciones y estándares exigidos."""
    model_config = ConfigDict(extra="ignore")

    cursos_dc3: list[str] = Field(
        default_factory=list,
        description="Cursos con constancia de habilidades laborales (DC-3) obligatorios",
    )
    porcentaje_dc3_inicial: float | None = Field(
        default=None,
        description="% del personal con DC-3 al presentar la propuesta",
    )
    plazo_dc3_completo_dias: int | None = Field(
        default=None,
        description="Días hábiles posteriores al fallo para completar el 100% de DC-3",
    )
    estandares_conocer: list[str] = Field(
        default_factory=list, description="Estándares de competencia exigidos"
    )
    cantidad_capacitadores_dc5: int | None = Field(
        default=None, description="Número total de capacitadores DC-5 (internos + externos)"
    )
    frecuencia_capacitacion_recurrente: str | None = Field(
        default=None, description="Ej. '2 veces por año'"
    )
    otras_certificaciones: list[str] = Field(
        default_factory=list, description="Otras certificaciones (ej. ISO 9001)"
    )


class AspectosTecnicos(BaseModel):
    """Qué se requiere técnicamente para cumplir el servicio."""
    model_config = ConfigDict(extra="ignore")

    servicio_solicitado: str = Field(
        default="", description="Descripción corta del servicio (ej. 'Vigilancia 24/7 en 3 sedes')"
    )
    numero_total_elementos: int | None = Field(
        default=None,
        description="Cantidad mínima de guardias (piso del contrato abierto). Si hay un solo número, ese.",
    )
    numero_total_elementos_maximo: int | None = Field(
        default=None,
        description="Cantidad máxima de guardias del contrato abierto. null si solo hay mínimo.",
    )
    personal_requerido: list[str] = Field(
        default_factory=list, description="Descripción libre del personal (turnos, perfil, etc.)"
    )
    distribucion_inmuebles: list[DistribucionInmueble] = Field(
        default_factory=list, description="Distribución estructurada de elementos por inmueble"
    )
    perfil_personal: PerfilPersonal = Field(default_factory=PerfilPersonal)
    equipo_supervision: EquipoSupervision = Field(default_factory=EquipoSupervision)
    alcance_servicio: AlcanceServicio = Field(default_factory=AlcanceServicio)
    capacitacion: Capacitacion = Field(default_factory=Capacitacion)
    # Operativos detallados
    tiempo_cobertura_faltas_minutos: int | None = Field(
        default=None, description="Minutos máximos para cubrir una falta de personal"
    )
    tolerancia_retardo_minutos: int | None = Field(
        default=None, description="Minutos de tolerancia antes de marcar retardo"
    )
    rondines_minimo_por_turno: int | None = Field(
        default=None, description="Cantidad mínima de rondines por turno"
    )
    permite_doblete_turno: bool | None = Field(
        default=None, description="¿Se permite que un guardia doble turno cuando no hay relevo?"
    )
    inventario_armas_minimo: int | None = Field(
        default=None, description="Cantidad mínima de armas registradas exigidas"
    )
    modalidades_permiso_federal: list[str] = Field(
        default_factory=list, description="Modalidades exigidas en el permiso federal de seguridad privada"
    )
    entidades_federativas_permiso_minimas: int | None = Field(
        default=None, description="Cantidad mínima de entidades federativas en el permiso"
    )
    requiere_oficina_local: bool | None = Field(
        default=None, description="¿Exige oficina física en una entidad específica?"
    )
    entidad_oficina_requerida: str | None = Field(
        default=None, description="Entidad federativa donde se exige oficina"
    )
    requiere_linea_telefonica_exclusiva: bool | None = Field(
        default=None, description="¿Exige línea telefónica dedicada?"
    )
    codigos_sectoriales: list[str] = Field(
        default_factory=list, description="Códigos o protocolos propios del sector (ej. hospitalario)"
    )
    examen_medico_frecuencia: str | None = Field(
        default=None, description="Frecuencia y vigencia exigida del certificado médico"
    )
    requiere_examen_psicometrico: bool | None = Field(
        default=None, description="¿Exige evaluación psicométrica vigente?"
    )
    requiere_examen_toxicologico: bool | None = Field(
        default=None, description="¿Exige examen toxicológico vigente?"
    )
    equipamiento_exigido: list[str] = Field(
        default_factory=list, description="Uniformes, radios, vehículos, cámaras, etc."
    )
    horarios_cobertura: str | None = Field(default=None, description="Ej. 'L-D 24x24'")
    sedes_o_ubicaciones: list[str] = Field(
        default_factory=list, description="Direcciones o nombres de las sedes a vigilar"
    )
    cobertura_geografica: list[str] = Field(
        default_factory=list, description="Entidades federativas cubiertas"
    )
    certificaciones_requeridas: list[str] = Field(
        default_factory=list,
        description="Obsoleto: usar capacitacion.otras_certificaciones. Se mantiene por compatibilidad.",
    )
    experiencia_minima_anios: int | None = None
    requisitos_tecnicos_listado: list[str] = Field(
        default_factory=list, description="Lista cruda de requisitos técnicos (sin clasificar)"
    )


class AspectosLegales(BaseModel):
    """Documentos, garantías, plazos y requisitos legales."""
    model_config = ConfigDict(extra="ignore")

    documentos_obligatorios: list[str] = Field(
        default_factory=list, description="Documentos que el participante debe presentar"
    )
    garantia_cumplimiento_pct: float | None = Field(
        default=None, description="Porcentaje del monto del contrato a garantizar"
    )
    garantia_seriedad_pct: float | None = None
    plazos_entrega_dias: int | None = None
    fecha_apertura: datetime | None = None
    fecha_junta_aclaraciones: datetime | None = None
    fecha_fallo: datetime | None = None
    fecha_firma_contrato: datetime | None = None
    fecha_visita_obligatoria: datetime | None = Field(
        default=None, description="Fecha de visita obligatoria a instalaciones, si aplica"
    )
    requiere_visita_obligatoria: bool | None = Field(
        default=None, description="¿La convocatoria exige visita previa obligatoria?"
    )
    dias_entrega_garantia_tras_firma: int | None = Field(
        default=None, description="Días naturales tras la firma para entregar la garantía"
    )
    plataforma_electronica: str | None = Field(
        default=None, description="Plataforma donde se presenta la propuesta"
    )
    plazo_contrato: str | None = Field(default=None, description="Duración del contrato")
    vigencia_servicio: str | None = Field(
        default=None, description="Vigencia del servicio (puede diferir del plazo contractual)"
    )
    ley_aplicable: str | None = None
    permite_mipymes: bool | None = None
    permite_participacion_conjunta: bool | None = None
    requisitos_legales_listado: list[str] = Field(
        default_factory=list, description="Lista cruda de requisitos legales (sin clasificar)"
    )


class AspectosEconomicos(BaseModel):
    """Montos, moneda y forma de pago."""
    model_config = ConfigDict(extra="ignore")

    monto_minimo: float | None = None
    monto_maximo: float | None = None
    presupuesto_autorizado: float | None = None
    moneda: str = "MXN"
    forma_pago: str | None = None
    anticipo: bool | None = None
    anticipo_pct: float | None = None
    tipo_contrato: str | None = Field(
        default=None, description="Ej. 'Abierto por monto', 'Cerrado', 'Plurianual'"
    )
    es_plurianual: bool | None = None
    pena_convencional_pct_dia: float | None = Field(
        default=None, description="% de pena convencional por día natural de atraso"
    )
    poliza_responsabilidad_civil_pct: float | None = Field(
        default=None, description="% del monto máximo a cubrir con póliza de responsabilidad civil"
    )
    dias_pago_deducible_robo: int | None = Field(
        default=None, description="Días hábiles para pagar el deducible por robo sin violencia"
    )
    deductivas_descripcion: list[str] = Field(
        default_factory=list, description="Descripción de deductivas específicas"
    )
    requisitos_economicos_listado: list[str] = Field(
        default_factory=list, description="Lista cruda de requisitos económicos (sin clasificar)"
    )


class RiesgoOportunidad(BaseModel):
    """Un punto de atención (riesgo u oportunidad) con traza a la fuente."""
    model_config = ConfigDict(extra="ignore")

    tipo: Literal["riesgo", "oportunidad", "observacion"]
    descripcion: str
    severidad: Literal["alta", "media", "baja"] = "media"
    fuentes: list[str] = Field(
        default_factory=list, description="Archivos en los que se basa la afirmación"
    )
    cita_literal: str | None = Field(
        default=None, description="Texto exacto del documento que respalda la afirmación"
    )


class CitaClave(BaseModel):
    """Referencia a un dato extraído con su fuente, para verificación."""
    model_config = ConfigDict(extra="ignore")

    campo: str = Field(..., description="Nombre del campo de la ficha")
    valor: str = Field(..., description="Valor extraído, como texto")
    fuente: str = Field(..., description="Nombre del archivo donde se encontró")
    cita_literal: str = Field(..., description="Texto exacto del documento")


class EvaluacionCumplimiento(BaseModel):
    """Evaluación sobre si es factible participar."""
    model_config = ConfigDict(extra="ignore")

    cumplimos_requisitos: bool | None = Field(
        default=None,
        description="True si parece factible participar, None si no hay información suficiente",
    )
    confianza_evaluacion: Literal["alta", "media", "baja"] = "media"
    razonamiento: str = Field(default="", description="Justificación breve en 2 a 4 oraciones")
    tipo_evaluacion: Literal["binaria", "puntos_y_porcentajes", "otro"] | None = Field(
        default=None, description="Cómo se evaluarán las propuestas según la convocatoria"
    )
    puntos_criticos: list[RiesgoOportunidad] = Field(default_factory=list)
    partidas_no_vigilancia_detectadas: list[str] = Field(
        default_factory=list,
        description="Partidas ajenas a vigilancia, si el expediente es mixto",
    )


class FichaTecnica(BaseModel):
    """Ficha técnica consolidada de una convocatoria.

    El orden de los campos es intencional: evaluación y citas van antes de
    las listas largas.
    """
    model_config = ConfigDict(extra="ignore")

    identificacion: IdentificacionFicha

    evaluacion: EvaluacionCumplimiento = Field(default_factory=EvaluacionCumplimiento)
    citas_clave: list[CitaClave] = Field(
        default_factory=list,
        description="Citas textuales de datos importantes con su archivo fuente",
    )

    tecnicos: AspectosTecnicos = Field(default_factory=AspectosTecnicos)
    legales: AspectosLegales = Field(default_factory=AspectosLegales)
    economicos: AspectosEconomicos = Field(default_factory=AspectosEconomicos)

    # Metadata de generación
    modelo_usado: str = ""
    archivos_procesados: list[str] = Field(default_factory=list)
    timestamp_generacion: datetime | None = None
    errores_extraccion: list[str] = Field(default_factory=list)
