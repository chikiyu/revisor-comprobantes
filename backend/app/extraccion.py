"""Del PDF al texto, y del texto a datos con un LLM."""

import io
import json
import os

from openai import APIError, OpenAI
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from .esquemas import DatosExtraidos

PROMPT = """Eres un asistente contable peruano. Del texto de un comprobante de pago
electrónico (factura o boleta) extrae los datos y responde SOLO con un JSON con estas claves:
ruc_emisor, razon_social, serie_numero, fecha (AAAA-MM-DD), moneda (PEN o USD),
subtotal_gravado, igv, otros_montos (exonerado + inafecto + ISC; 0 si no hay), total,
categoria (una de: combustible, peaje, mantenimiento, otros).
Los montos van como números con punto decimal. No inventes datos: copia lo que dice el texto."""


class ErrorDeLectura(Exception):
    """El documento o la respuesta de la IA no sirven (culpa del dato)."""


class ErrorDeProveedor(Exception):
    """No se pudo hablar con el proveedor de IA (clave, modelo, límite, red)."""


def texto_de_pdf(contenido: bytes) -> str:
    try:
        texto = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(contenido)).pages)
    except PyPdfError as e:  # archivo dañado, con contraseña, o que no es un PDF
        raise ErrorDeLectura("No se pudo leer el PDF: está dañado o protegido") from e
    if not texto.strip():
        # PDF escaneado (imagen): necesitaría OCR, que este proyecto no hace
        raise ErrorDeLectura("El PDF no tiene texto seleccionable (¿es un escaneo?)")
    return texto


def cliente_llm() -> OpenAI:
    """Cualquier proveedor compatible con la API de OpenAI: OpenAI, Groq u Ollama."""
    return OpenAI(base_url=os.getenv("LLM_BASE_URL"), api_key=os.getenv("LLM_API_KEY", "ollama"))


def extraer_datos(texto: str, cliente: OpenAI | None = None) -> DatosExtraidos:
    cliente = cliente or cliente_llm()
    try:
        respuesta = cliente.chat.completions.create(
            model=os.getenv("LLM_MODELO", "openai/gpt-oss-120b"),
            temperature=0,
            max_completion_tokens=2000,  # los modelos de razonamiento gastan tokens pensando
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": texto}],
        )
    except APIError as e:
        raise ErrorDeProveedor(f"No se pudo consultar la IA: {e.__class__.__name__}") from e
    crudo = respuesta.choices[0].message.content or ""  # puede venir vacío si se cortó
    try:
        return DatosExtraidos.model_validate(json.loads(crudo))
    except (json.JSONDecodeError, ValueError) as e:
        raise ErrorDeLectura(f"La IA devolvió algo que no calza con el esquema: {e}") from e
