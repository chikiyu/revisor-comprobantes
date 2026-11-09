"""Forma de los datos. Pydantic rechaza lo que la IA devuelva mal formado."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# Mismos límites que las columnas de db.py: si la IA se pasa, se rechaza aquí con un
# 422 claro y no revienta PostgreSQL con un 500.
Monto = Annotated[Decimal, Field(ge=0, lt=Decimal("10000000000"))]


class Categoria(str, Enum):
    combustible = "combustible"
    peaje = "peaje"
    mantenimiento = "mantenimiento"  # repuestos, llantas, taller
    otros = "otros"


class DatosExtraidos(BaseModel):
    """Lo que se le pide a la IA. Si falta un campo o el tipo no calza, falla."""

    model_config = ConfigDict(coerce_numbers_to_str=True)  # el RUC puede llegar como número

    ruc_emisor: str = Field(max_length=11, description="RUC de 11 dígitos de quien emite")
    razon_social: str = Field(max_length=255)
    serie_numero: str = Field(max_length=20, description="por ejemplo F001-00012345")
    fecha: date
    moneda: Literal["PEN", "USD"] = "PEN"
    subtotal_gravado: Monto
    igv: Monto
    otros_montos: Monto = Field(default=Decimal("0"), description="exonerado, inafecto, ISC")
    total: Monto
    categoria: Categoria


class ComprobanteSalida(DatosExtraidos):
    id: int
    archivo: str
    observaciones: list[str]
    estado: str  # "ok" u "observado"

    model_config = ConfigDict(from_attributes=True)
