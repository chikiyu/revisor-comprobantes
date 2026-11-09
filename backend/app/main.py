"""API REST. Documentación automática en /docs (Swagger)."""

import csv
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from .db import Comprobante, Sesion, crear_tablas
from .esquemas import ComprobanteSalida
from .extraccion import ErrorDeLectura, ErrorDeProveedor, extraer_datos, texto_de_pdf
from .validacion import validar


@asynccontextmanager
async def inicio(app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(title="Revisor de comprobantes con IA", lifespan=inicio)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"])


@app.post("/comprobantes", response_model=ComprobanteSalida, status_code=201)
def subir(archivo: UploadFile):  # sin async: FastAPI la corre en otro hilo y la llamada lenta a la IA no bloquea el servidor
    if archivo.content_type != "application/pdf":
        raise HTTPException(415, "Solo se aceptan PDF")
    try:
        datos = extraer_datos(texto_de_pdf(archivo.file.read()))
    except ErrorDeLectura as e:
        raise HTTPException(422, str(e))
    except ErrorDeProveedor as e:
        raise HTTPException(502, str(e))

    obs = validar(datos.model_dump())
    fila = Comprobante(
        archivo=(archivo.filename or "sin_nombre")[:255],
        **datos.model_dump(mode="python") | {"categoria": datos.categoria.value},
        observaciones=obs,
        estado="observado" if obs else "ok",
    )
    with Sesion() as s:
        s.add(fila)
        s.commit()
        s.refresh(fila)
        return ComprobanteSalida.model_validate(fila)


@app.get("/comprobantes", response_model=list[ComprobanteSalida])
def listar():
    with Sesion() as s:
        filas = s.scalars(select(Comprobante).order_by(Comprobante.id.desc())).all()
        return [ComprobanteSalida.model_validate(f) for f in filas]


@app.get("/comprobantes/export.csv")
def exportar():
    salida = io.StringIO()
    campos = ["id", "archivo", "ruc_emisor", "razon_social", "serie_numero", "fecha", "moneda",
              "subtotal_gravado", "igv", "otros_montos", "total", "categoria", "estado", "observaciones"]
    w = csv.writer(salida)
    w.writerow(campos)
    for c in listar():
        fila = c.model_dump()
        fila["observaciones"] = " | ".join(fila["observaciones"])
        w.writerow([fila[k] for k in campos])
    salida.seek(0)
    return StreamingResponse(salida, media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=comprobantes.csv"})
