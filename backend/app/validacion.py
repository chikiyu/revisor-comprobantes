"""Reglas que verifican lo que extrae la IA.

La IA lee el comprobante, pero no se le cree a ciegas: cada dato pasa por
reglas deterministas (RUC, serie, IGV, totales, fecha). Si algo no cuadra,
se devuelve una observación en lugar de corregirlo en silencio.
"""

import re
from datetime import date
from decimal import Decimal

TASA_IGV = Decimal("0.18")
TOLERANCIA = Decimal("0.02")  # redondeos de céntimos en los comprobantes reales

PESOS_RUC = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
PREFIJOS_RUC = ("10", "15", "17", "20")  # persona natural, no domiciliado, etc., empresa
SERIE_NUMERO = re.compile(r"^[FBE][A-Z0-9]{3}-\d{1,8}$")


def ruc_valido(ruc: str) -> bool:
    """Valida un RUC peruano con su dígito verificador (módulo 11)."""
    if not (len(ruc) == 11 and ruc.isdigit() and ruc[:2] in PREFIJOS_RUC):
        return False
    suma = sum(int(d) * p for d, p in zip(ruc[:10], PESOS_RUC))
    verificador = 11 - suma % 11
    if verificador == 10:
        verificador = 0
    elif verificador == 11:
        verificador = 1
    return verificador == int(ruc[10])


def validar(c: dict, hoy: date | None = None) -> list[str]:
    """Devuelve la lista de observaciones; vacía si el comprobante cuadra.

    `c` trae: ruc_emisor, serie_numero, fecha (date), subtotal_gravado,
    igv, otros_montos y total (Decimal).
    """
    hoy = hoy or date.today()
    obs = []

    if not ruc_valido(c["ruc_emisor"]):
        obs.append(f"RUC del emisor inválido: {c['ruc_emisor']}")

    if not SERIE_NUMERO.match(c["serie_numero"]):
        obs.append(f"Serie y número con formato raro: {c['serie_numero']}")

    if c["fecha"] > hoy:
        obs.append(f"La fecha de emisión ({c['fecha']}) está en el futuro")

    igv_esperado = (c["subtotal_gravado"] * TASA_IGV).quantize(Decimal("0.01"))
    if abs(c["igv"] - igv_esperado) > TOLERANCIA:
        obs.append(f"IGV no cuadra: dice {c['igv']:.2f}, el 18 % del gravado es {igv_esperado}")

    suma = c["subtotal_gravado"] + c["igv"] + c["otros_montos"]
    if abs(c["total"] - suma) > TOLERANCIA:
        obs.append(f"Total no cuadra: dice {c['total']:.2f}, la suma de las partes da {suma:.2f}")

    return obs
