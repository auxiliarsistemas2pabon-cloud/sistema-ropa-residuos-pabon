from datetime import date, time
from decimal import Decimal

import pytest
from django.urls import reverse

from core.models import GestorExterno
from movimientos.models import Movimiento, Pesaje, TipoMovimiento
from residuos.models import CategoriaResiduo, DetalleResiduo, EntregaGestor

pytestmark = pytest.mark.django_db

DIA = date(2026, 3, 10)


@pytest.fixture
def datos_ropa(crear_movimiento, usuario, sede, area):
    mov = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=DIA, hora=time(10, 0))
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("11.20"), tara=0, pesado_por=usuario)
    return mov


def test_usuario_no_puede_ver_consolidados(api_client, usuario):
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-consolidado", args=["ropa_por_servicio"]))
    assert resp.status_code == 403


def test_consolidado_ropa_por_servicio(api_client, administradora, datos_ropa, sede):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-consolidado", args=["ropa_por_servicio"]), {"sede": sede.pk})
    assert resp.status_code == 200
    assert resp.data["filas"][0]["kg"] == Decimal("11.20")


def test_consolidado_ropa_por_sede_trae_total(api_client, administradora, datos_ropa):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-consolidado", args=["ropa_por_sede"]))
    assert resp.status_code == 200
    assert resp.data["total"] == Decimal("11.20")


def test_consolidado_clave_desconocida_404(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-consolidado", args=["inventado"]))
    assert resp.status_code == 404


def test_rh1_del_mes_suma_por_dia(api_client, administradora, crear_movimiento):
    bio = CategoriaResiduo.objects.get(nombre="Biosanitarios")
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=DIA, hora=time(9, 0))
    DetalleResiduo.objects.create(movimiento=mov, categoria_residuo=bio, peso_kg=Decimal("4.00"))

    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-rh1"), {"mes": "2026-03"})
    assert resp.status_code == 200
    assert len(resp.data["filas"]) == 31
    assert resp.data["total_mes"] == Decimal("4.00")
    assert any(c["nombre"] == "Biosanitarios" for c in resp.data["columnas"])


def test_facturacion_resumen_separa_pendientes(api_client, administradora, crear_movimiento, usuario):
    from datetime import datetime, timezone as dt_timezone

    gestor = GestorExterno.objects.create(nombre="SALVI S.A.S.", nit="900123456", tarifa_kg_vigente=Decimal("2500"))

    def _entrega(periodo, kg, valor, creada_en):
        mov = crear_movimiento(
            tipo=TipoMovimiento.RESIDUO_RECOLECCION, fecha=periodo, hora=time(9, 0), periodo_facturacion=periodo,
        )
        Movimiento.objects.filter(pk=mov.pk).update(creado_en=creada_en)
        Pesaje.objects.create(movimiento=mov, peso_total=Decimal(kg), tara=0, pesado_por=usuario)
        return EntregaGestor.objects.create(
            movimiento=mov, gestor_externo=gestor, numero_factura="F1",
            kg_facturados=Decimal(kg), valor_facturado=Decimal(valor),
        )

    _entrega(date(2026, 3, 1), "10.00", "25000", datetime(2026, 3, 20, tzinfo=dt_timezone.utc))
    _entrega(date(2026, 2, 1), "6.00", "15000", datetime(2026, 3, 5, tzinfo=dt_timezone.utc))

    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-facturacion-resumen"), {"mes": "2026-03"})
    assert resp.status_code == 200
    assert resp.data["total_actual"] == Decimal("25000")
    assert resp.data["total_pendientes"] == Decimal("15000")


def test_facturacion_conciliacion_marca_diferencia(api_client, administradora, crear_movimiento, usuario):
    gestor = GestorExterno.objects.create(nombre="SALVI S.A.S.", nit="900654321", tarifa_kg_vigente=Decimal("2500"))
    mov = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_RECOLECCION, fecha=DIA, hora=time(9, 0), periodo_facturacion=date(2026, 3, 1),
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("10.30"), tara=Decimal("0.30"), pesado_por=usuario)
    EntregaGestor.objects.create(
        movimiento=mov, gestor_externo=gestor, numero_factura="F9",
        kg_facturados=Decimal("9.00"), valor_facturado=Decimal("1000"),
    )

    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-facturacion-conciliacion"), {"mes": "2026-03"})
    assert resp.status_code == 200
    assert resp.data["filas"][0]["diferencia"] == Decimal("1.00")


def test_xlsx_export_alias_funciona_bajo_api(api_client, administradora, datos_ropa):
    # exportar() es una vista de Django clásica (no DRF): fuerza sesión real
    # con force_login, no force_authenticate (que solo lo respeta el request
    # de DRF, no el AuthenticationMiddleware normal).
    api_client.force_login(administradora)
    resp = api_client.get(reverse("api-consolidado-exportar", args=["ropa_por_servicio"]))
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
