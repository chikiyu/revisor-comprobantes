"""Prueba con el LLM de verdad. Gasta cuota y necesita internet, así que no corre por defecto.

Uso, desde backend/:  set -a; . ../.env; set +a; ../.venv/bin/pytest -m integracion -v
"""

import os
from pathlib import Path

import pytest

from app.extraccion import extraer_datos, texto_de_pdf
from app.validacion import validar

EJEMPLOS = Path(__file__).parents[2] / "ejemplos"

pytestmark = [
    pytest.mark.integracion,
    pytest.mark.skipif(not os.getenv("LLM_API_KEY"), reason="falta LLM_API_KEY"),
]


@pytest.mark.parametrize("archivo, ruc, serie, total, categoria, observacion", [
    ("factura_grifo_ok.pdf", "20999999990", "F001-00004521", "600", "combustible", None),
    ("factura_repuestos_igv_mal.pdf", "20888888889", "F002-00000877", "420", "mantenimiento", "IGV"),
    ("factura_peaje_ruc_malo.pdf", "20777777770", "F010-00123456", "30", "peaje", "RUC"),
])
def test_pdf_real_con_llm_real(archivo, ruc, serie, total, categoria, observacion):
    datos = extraer_datos(texto_de_pdf((EJEMPLOS / archivo).read_bytes()))
    assert datos.ruc_emisor == ruc
    assert datos.serie_numero == serie
    assert float(datos.total) == float(total)
    assert datos.categoria.value == categoria

    obs = validar(datos.model_dump())
    if observacion is None:
        assert obs == []
    else:
        assert len(obs) == 1 and observacion in obs[0]
