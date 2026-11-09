"""Prueba la API completa sin llamar a ninguna IA: se reemplaza el LLM por uno falso."""

import os

os.environ["DATABASE_URL"] = "sqlite://"  # base en memoria para las pruebas

from datetime import date  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import db, main  # noqa: E402
from app.esquemas import DatosExtraidos  # noqa: E402


@pytest.fixture
def cliente(monkeypatch):
    # SQLite en memoria con una sola conexión compartida, para que la tabla no desaparezca
    motor = db.create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    monkeypatch.setattr(db, "motor", motor)
    monkeypatch.setattr(main, "Sesion", db.sessionmaker(motor))
    db.Base.metadata.create_all(motor)
    monkeypatch.setattr(main, "texto_de_pdf", lambda contenido: "texto falso")
    monkeypatch.setattr(main, "extraer_datos", lambda texto: DatosExtraidos(
        ruc_emisor="20131312955", razon_social="Grifo de prueba", serie_numero="F001-00000001",
        fecha=date(2026, 11, 2), subtotal_gravado=Decimal("100"), igv=Decimal("20"),
        total=Decimal("120"), categoria="combustible"))
    return TestClient(main.app)


def test_sube_y_marca_igv_malo(cliente):
    r = cliente.post("/comprobantes", files={"archivo": ("f.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["estado"] == "observado"
    assert any("IGV" in o for o in cuerpo["observaciones"])
    assert len(cliente.get("/comprobantes").json()) == 1


def test_rechaza_lo_que_no_es_pdf(cliente):
    r = cliente.post("/comprobantes", files={"archivo": ("f.txt", b"hola", "text/plain")})
    assert r.status_code == 415


def test_exporta_csv(cliente):
    cliente.post("/comprobantes", files={"archivo": ("f.pdf", b"%PDF", "application/pdf")})
    r = cliente.get("/comprobantes/export.csv")
    assert r.status_code == 200
    assert "ruc_emisor" in r.text.splitlines()[0]


def test_si_el_proveedor_falla_responde_502(cliente, monkeypatch):
    def falla(texto):
        raise main.ErrorDeProveedor("sin servicio")

    monkeypatch.setattr(main, "extraer_datos", falla)
    r = cliente.post("/comprobantes", files={"archivo": ("f.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 502
