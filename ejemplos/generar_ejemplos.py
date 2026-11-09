"""Genera facturas ficticias en PDF para probar el revisor.

Uso: pip install fpdf2 && python ejemplos/generar_ejemplos.py
Crea tres: una correcta, una con el IGV mal calculado y una con RUC inválido.
"""

from pathlib import Path

from fpdf import FPDF

CARPETA = Path(__file__).parent

EJEMPLOS = {
    "factura_grifo_ok.pdf": dict(
        ruc="20999999990", razon="GRIFO EL EJEMPLO S.A.C.", serie="F001-00004521", fecha="02/11/2026",
        detalle="PETROLEO DIESEL B5 S50 - 45.50 GAL", gravado="508.47", igv="91.53", total="600.00"),
    "factura_repuestos_igv_mal.pdf": dict(
        ruc="20888888889", razon="REPUESTOS FICTICIOS DEL SUR E.I.R.L.", serie="F002-00000877",
        fecha="28/10/2026", detalle="JUEGO DE PASTILLAS DE FRENO + FILTRO DE ACEITE",
        gravado="350.00", igv="70.00", total="420.00"),
    "factura_peaje_ruc_malo.pdf": dict(
        ruc="20777777770", razon="CONCESIONARIA VIAL DE PRUEBA S.A.", serie="F010-00123456",
        fecha="30/10/2026", detalle="PEAJE - VEHICULO PESADO 3 EJES", gravado="25.42", igv="4.58",
        total="30.00"),
}


def generar(nombre: str, d: dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, d["razon"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, f"RUC: {d['ruc']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "FACTURA ELECTRONICA", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"{d['serie']}    Fecha de emision: {d['fecha']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Cliente: TRANSPORTES DE PRUEBA S.R.L. - Moneda: SOLES", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.cell(0, 6, f"Descripcion: {d['detalle']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    for etiqueta, clave in (("Op. Gravada", "gravado"), ("IGV 18%", "igv"), ("Importe Total", "total")):
        pdf.cell(0, 6, f"{etiqueta}: S/ {d[clave]}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "EJEMPLO FICTICIO GENERADO PARA PRUEBAS - NO ES UN COMPROBANTE REAL")
    pdf.output(str(CARPETA / nombre))


if __name__ == "__main__":
    for nombre, datos in EJEMPLOS.items():
        generar(nombre, datos)
        print("creado", nombre)
