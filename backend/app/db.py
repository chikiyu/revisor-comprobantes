"""Base de datos: PostgreSQL con Docker; SQLite si corres el backend suelto."""

import os
from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

URL = os.getenv("DATABASE_URL", "sqlite:///./comprobantes.db")
motor = create_engine(URL)
Sesion = sessionmaker(motor)


class Base(DeclarativeBase):
    pass


class Comprobante(Base):
    __tablename__ = "comprobantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    archivo: Mapped[str] = mapped_column(String(255))
    ruc_emisor: Mapped[str] = mapped_column(String(11))
    razon_social: Mapped[str] = mapped_column(String(255))
    serie_numero: Mapped[str] = mapped_column(String(20))
    fecha: Mapped[date]
    moneda: Mapped[str] = mapped_column(String(3))
    subtotal_gravado: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    igv: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    otros_montos: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    categoria: Mapped[str] = mapped_column(String(20))
    observaciones: Mapped[list] = mapped_column(JSON)
    estado: Mapped[str] = mapped_column(String(10))


def crear_tablas():
    Base.metadata.create_all(motor)
