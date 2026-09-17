"""Carga y validación del dataset simulado (`demo_data/*.json`).

Todo es local: se leen tres archivos JSON y se validan con Pydantic. Si algo no
cuadra se lanza `DatasetInvalido` con una lista de errores legible, y la UI la
muestra en lugar de la app.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from monitor_demo.esquemas import FichaTecnica

DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data"
PREFIJO_ID = "DEMO-"
MARCAS_FICTICIAS = ("(ficticio)", "(ficticia)")
# Mismo criterio que el sistema real: pocos caracteres por página = PDF escaneado.
UMBRAL_CHARS_POR_PAGINA = 50

TipoDocumento = Literal[
    "Convocatoria",
    "Anexo técnico",
    "Modelo de contrato",
    "Acta de junta de aclaraciones",
    "Relación de inmuebles",
    "Formato de propuesta económica",
    "Oficio de suficiencia presupuestal",
]
Estatus = Literal["Vigente", "Recepción de proposiciones", "En evaluación", "Fallo emitido"]
ETAPAS = ("descarga", "clasificacion", "ocr", "extraccion", "ficha")


class DatasetInvalido(Exception):
    """El dataset simulado no pasó la validación."""

    def __init__(self, origen: str, errores: list[str]):
        self.origen = origen
        self.errores = errores
        super().__init__(f"{origen}: {len(errores)} error(es)")


class TiemposSimulados(BaseModel):
    """Segundos simulados por etapa para un documento."""
    model_config = ConfigDict(extra="forbid")

    descarga_seg: float = Field(ge=0)
    clasificacion_seg: float = Field(ge=0)
    ocr_seg: float = Field(ge=0)
    extraccion_seg: float = Field(ge=0)

    @property
    def total(self) -> float:
        return self.descarga_seg + self.clasificacion_seg + self.ocr_seg + self.extraccion_seg


class DocumentoDemo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=3)
    tipo: TipoDocumento
    formato: Literal["pdf", "docx"]
    paginas: int = Field(ge=1, le=400)
    tamano_kb: int = Field(gt=0)
    clasificacion: Literal["texto", "escaneado"]
    chars_por_pagina: int = Field(ge=0)
    tiempos: TiemposSimulados

    @property
    def escaneado(self) -> bool:
        return self.clasificacion == "escaneado"

    @model_validator(mode="after")
    def _coherencia(self) -> DocumentoDemo:
        if not self.nombre.lower().endswith(f".{self.formato}"):
            raise ValueError(f"'{self.nombre}' no termina en .{self.formato}")
        if self.formato != "pdf" and self.escaneado:
            raise ValueError(f"'{self.nombre}': solo un PDF puede clasificarse como escaneado")
        if self.formato == "pdf":
            bajo_umbral = self.chars_por_pagina < UMBRAL_CHARS_POR_PAGINA
            if bajo_umbral != self.escaneado:
                raise ValueError(
                    f"'{self.nombre}': {self.chars_por_pagina} caracteres por página no concuerda "
                    f"con la clasificación '{self.clasificacion}' (umbral {UMBRAL_CHARS_POR_PAGINA})"
                )
        if self.escaneado and self.tiempos.ocr_seg <= 0:
            raise ValueError(f"'{self.nombre}': un escaneado necesita tiempo de OCR")
        if not self.escaneado and self.tiempos.ocr_seg > 0:
            raise ValueError(f"'{self.nombre}': un documento con texto no pasa por OCR")
        return self


class ExpedienteDemo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    codigo_expediente: str
    nombre_procedimiento: str
    dependencia: str
    siglas: str
    unidad_compradora: str
    entidad_federativa: str
    tipo_procedimiento: str
    caracter: str
    estatus: Estatus
    partidas: list[str] = Field(min_length=1)
    fecha_publicacion: date
    fecha_junta_aclaraciones: datetime
    fecha_apertura: datetime
    fecha_fallo: datetime
    monto_minimo: float | None = Field(default=None, ge=0)
    monto_maximo: float = Field(gt=0)
    numero_guardias: int = Field(gt=0)
    numero_guardias_maximo: int | None = None
    turnos: list[str] = Field(min_length=1)
    documentos: list[DocumentoDemo] = Field(min_length=3, max_length=7)
    tiempo_ficha_seg: float = Field(gt=0)

    @field_validator("id", "codigo_expediente")
    @classmethod
    def _prefijo_demo(cls, valor: str) -> str:
        if not valor.startswith(PREFIJO_ID):
            raise ValueError(f"los identificadores deben empezar con '{PREFIJO_ID}'")
        return valor

    @field_validator("dependencia", "unidad_compradora")
    @classmethod
    def _marcada_como_ficticia(cls, valor: str) -> str:
        if not valor.endswith(MARCAS_FICTICIAS):
            raise ValueError("toda dependencia o unidad debe marcarse como '(ficticio)' o '(ficticia)'")
        return valor

    @model_validator(mode="after")
    def _coherencia(self) -> ExpedienteDemo:
        fechas = [
            self.fecha_publicacion,
            self.fecha_junta_aclaraciones.date(),
            self.fecha_apertura.date(),
            self.fecha_fallo.date(),
        ]
        if any(f.year != 2026 for f in fechas):
            raise ValueError(f"{self.id}: todas las fechas del dataset deben ser de 2026")
        if fechas != sorted(fechas):
            raise ValueError(f"{self.id}: el orden publicación → junta → apertura → fallo no es cronológico")
        if self.monto_minimo is not None and self.monto_minimo > self.monto_maximo:
            raise ValueError(f"{self.id}: monto mínimo mayor que el máximo")
        if self.numero_guardias_maximo is not None and self.numero_guardias_maximo < self.numero_guardias:
            raise ValueError(f"{self.id}: guardias máximos menor que el mínimo")
        nombres = [d.nombre for d in self.documentos]
        if len(nombres) != len(set(nombres)):
            raise ValueError(f"{self.id}: hay documentos con nombre repetido")
        return self

    @property
    def total_escaneados(self) -> int:
        return sum(1 for d in self.documentos if d.escaneado)

    @property
    def total_paginas(self) -> int:
        return sum(d.paginas for d in self.documentos)

    def tiempos_por_etapa(self) -> dict[str, float]:
        return {
            "descarga": sum(d.tiempos.descarga_seg for d in self.documentos),
            "clasificacion": sum(d.tiempos.clasificacion_seg for d in self.documentos),
            "ocr": sum(d.tiempos.ocr_seg for d in self.documentos),
            "extraccion": sum(d.tiempos.extraccion_seg for d in self.documentos),
            "ficha": self.tiempo_ficha_seg,
        }


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    fecha_corte: date
    descripcion: str
    expedientes: list[ExpedienteDemo] = Field(min_length=12, max_length=17)
    textos: dict[str, dict[str, str]]
    fichas: dict[str, FichaTecnica]

    @model_validator(mode="after")
    def _referencias_cruzadas(self) -> Dataset:
        errores: list[str] = []
        ids = [e.id for e in self.expedientes]
        if len(ids) != len(set(ids)):
            errores.append("hay IDs de expediente repetidos")
        sobrantes = (set(self.textos) | set(self.fichas)) - set(ids)
        if sobrantes:
            errores.append(f"textos o fichas para expedientes inexistentes: {sorted(sobrantes)}")

        for exp in self.expedientes:
            nombres = {d.nombre for d in exp.documentos}
            textos = self.textos.get(exp.id)
            if textos is None:
                errores.append(f"{exp.id}: falta el texto extraído")
                continue
            if set(textos) != nombres:
                errores.append(f"{exp.id}: los textos no corresponden a los documentos del expediente")
            ficha = self.fichas.get(exp.id)
            if ficha is None:
                errores.append(f"{exp.id}: falta la ficha técnica")
                continue
            if ficha.identificacion.numero_procedimiento != exp.id:
                errores.append(f"{exp.id}: la ficha apunta a otro número de procedimiento")
            if set(ficha.archivos_procesados) != nombres:
                errores.append(f"{exp.id}: archivos procesados de la ficha ≠ documentos del expediente")
            # Cada cita debe existir, literal, en el texto del archivo que menciona.
            citas = [(c.fuente, c.cita_literal) for c in ficha.citas_clave]
            for punto in ficha.evaluacion.puntos_criticos:
                if punto.cita_literal:
                    citas.extend((f, punto.cita_literal) for f in punto.fuentes)
            for fuente, cita in citas:
                if cita not in textos.get(fuente, ""):
                    errores.append(f"{exp.id}: la cita «{cita[:40]}…» no aparece en '{fuente}'")
        if errores:
            raise ValueError("; ".join(errores))
        return self

    def expediente(self, id_expediente: str) -> ExpedienteDemo:
        return next(e for e in self.expedientes if e.id == id_expediente)


def _leer_json(ruta: Path) -> object:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise DatasetInvalido(ruta.name, [f"No se encontró el archivo demo_data/{ruta.name}"]) from None
    except json.JSONDecodeError as exc:
        raise DatasetInvalido(
            ruta.name, [f"JSON mal formado (línea {exc.lineno}, columna {exc.colno}): {exc.msg}"]
        ) from None


def _formatear(exc: ValidationError) -> list[str]:
    errores = []
    for err in exc.errors(include_url=False):
        ubicacion = " → ".join(str(p) for p in err["loc"]) or "raíz"
        mensaje = err["msg"].removeprefix("Value error, ")
        errores.append(f"{ubicacion}: {mensaje}")
    return errores


def validar_dataset(directorio: Path = DATA_DIR) -> Dataset:
    """Lee los tres JSON y devuelve el dataset validado o lanza `DatasetInvalido`."""
    base = _leer_json(directorio / "expedientes.json")
    if not isinstance(base, dict):
        raise DatasetInvalido("expedientes.json", ["Se esperaba un objeto JSON en la raíz"])
    crudo = {
        **base,
        "textos": _leer_json(directorio / "textos.json"),
        "fichas": _leer_json(directorio / "fichas.json"),
    }
    try:
        return Dataset.model_validate(crudo)
    except ValidationError as exc:
        raise DatasetInvalido("demo_data/", _formatear(exc)) from None
