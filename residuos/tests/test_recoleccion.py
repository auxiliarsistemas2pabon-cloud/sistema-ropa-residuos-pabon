from decimal import Decimal

import pytest
from django.urls import reverse

from movimientos.models import Movimiento, TipoMovimiento
from residuos.models import CategoriaResiduo

pytestmark = pytest.mark.django_db


def test_post_valido_crea_recoleccion_con_bolsas_y_dos_responsables(client, usuario, sede, area):
    no_aprovechables = CategoriaResiduo.objects.get(nombre="No aprovechables")
    client.force_login(usuario)
    resp = client.post(
        reverse("residuos:recoleccion"),
        {
            "sede": sede.pk,
            "servicio": area.pk,
            "grupo": "NO_PELIGROSO",
            "categoria": no_aprovechables.pk,
            "tipo_especifico": "",
            "peso_total": "9.00",
            "tara": "0.40",
            "cantidad_bolsas": "3",
            "entrega_por": usuario.pk,
            "recibe_por": usuario.pk,
            "observaciones": "",
        },
    )
    assert resp.status_code == 302

    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.RESIDUO_RECOLECCION)
    assert mov.recibe_por == usuario
    detalle = mov.detalles_residuo.get()
    assert detalle.peso_kg == Decimal("8.60")
    assert detalle.cantidad_bolsas == 3
