from datetime import date
from decimal import Decimal

from app.validacion import ruc_valido, validar

HOY = date(2026, 11, 7)


def comprobante(**cambios):
    base = dict(
        ruc_emisor="20131312955",  # RUC público de la SUNAT
        serie_numero="F001-00012345",
        fecha=date(2026, 11, 2),
        subtotal_gravado=Decimal("100.00"),
        igv=Decimal("18.00"),
        otros_montos=Decimal("0.00"),
        total=Decimal("118.00"),
    )
    base.update(cambios)
    return base


def test_ruc_correcto():
    assert ruc_valido("20131312955")


def test_ruc_digito_verificador_malo():
    assert not ruc_valido("20131312954")


def test_ruc_largo_o_prefijo_malo():
    assert not ruc_valido("2013131295")
    assert not ruc_valido("30131312955")


def test_comprobante_que_cuadra_no_tiene_observaciones():
    assert validar(comprobante(), HOY) == []


def test_igv_mal_calculado():
    obs = validar(comprobante(igv=Decimal("19.00"), total=Decimal("119.00")), HOY)
    assert any("IGV" in o for o in obs)


def test_total_que_no_suma():
    obs = validar(comprobante(total=Decimal("120.00")), HOY)
    assert any("Total" in o for o in obs)


def test_redondeo_de_centimos_se_tolera():
    c = comprobante(subtotal_gravado=Decimal("84.75"), igv=Decimal("15.26"), total=Decimal("100.01"))
    assert validar(c, HOY) == []


def test_fecha_futura_y_serie_rara():
    obs = validar(comprobante(fecha=date(2026, 12, 1), serie_numero="12345"), HOY)
    assert len(obs) == 2
