"""Prueba extraccion.py sin internet: el PDF es real, el cliente del LLM es falso."""

import io
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError
from pypdf import PdfWriter

from app.extraccion import ErrorDeLectura, ErrorDeProveedor, extraer_datos, texto_de_pdf

EJEMPLOS = Path(__file__).parents[2] / "ejemplos"

BUENO = {
    "ruc_emisor": "20999999990", "razon_social": "GRIFO", "serie_numero": "F001-00004521",
    "fecha": "2026-11-02", "moneda": "PEN", "subtotal_gravado": 508.47, "igv": 91.53,
    "otros_montos": 0, "total": 600.00, "categoria": "combustible",
}


class ClienteFalso:
    """Imita client.chat.completions.create y guarda con qué lo llamaron."""

    def __init__(self, contenido=None, error=None):
        self.contenido, self.error, self.pedido = contenido, error, None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))

    def _crear(self, **pedido):
        self.pedido = pedido
        if self.error:
            raise self.error
        mensaje = SimpleNamespace(content=self.contenido)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)])


def test_lee_el_texto_de_un_pdf_real():
    texto = texto_de_pdf((EJEMPLOS / "factura_grifo_ok.pdf").read_bytes())
    assert "20999999990" in texto and "600.00" in texto


def test_pdf_sin_texto_se_rechaza():
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    salida = io.BytesIO()
    escritor.write(salida)
    with pytest.raises(ErrorDeLectura):
        texto_de_pdf(salida.getvalue())


@pytest.mark.parametrize("contenido", [b"esto no es un pdf", b"%PDF-1.7 cortado"])
def test_pdf_danado_se_rechaza(contenido):
    with pytest.raises(ErrorDeLectura):
        texto_de_pdf(contenido)


def test_ruc_que_llega_como_numero_se_acepta():
    datos = extraer_datos("texto", ClienteFalso(json.dumps(BUENO | {"ruc_emisor": 20999999990})))
    assert datos.ruc_emisor == "20999999990"


def test_convierte_la_respuesta_y_pide_json():
    cliente = ClienteFalso(json.dumps(BUENO))
    datos = extraer_datos("texto", cliente)
    assert str(datos.total) == "600.0" and datos.categoria.value == "combustible"
    assert cliente.pedido["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("contenido", [
    "esto no es json",
    None,  # respuesta vacía, por ejemplo si se cortó por tokens
    json.dumps({k: v for k, v in BUENO.items() if k != "total"}),  # falta un campo
    json.dumps(BUENO | {"categoria": "viajes"}),  # valor fuera del Enum
    json.dumps(BUENO | {"total": -5}),  # monto negativo
    json.dumps(BUENO | {"moneda": "SOLES"}),  # no cabe en la columna
    json.dumps(BUENO | {"ruc_emisor": "RUC 20999999990"}),  # más largo que la columna
    json.dumps(BUENO | {"serie_numero": "F" * 21}),
    json.dumps(BUENO | {"total": 1e11}),  # no cabe en numeric(12,2)
])
def test_respuesta_mala_de_la_ia_se_rechaza(contenido):
    with pytest.raises(ErrorDeLectura):
        extraer_datos("texto", ClienteFalso(contenido))


def test_fallo_del_proveedor():
    error = APIConnectionError(request=httpx.Request("POST", "http://x"))
    with pytest.raises(ErrorDeProveedor):
        extraer_datos("texto", ClienteFalso(error=error))
