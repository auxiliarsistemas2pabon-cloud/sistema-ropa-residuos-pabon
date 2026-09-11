from datetime import date, time

import pytest
from django.urls import reverse

from ..models import Novedad, TipoMovimiento, TipoNovedad

pytestmark = pytest.mark.django_db


def test_lista_novedades_filtra_por_tipo(api_client, usuario, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))
    Novedad.objects.create(movimiento=mov, tipo_novedad=TipoNovedad.DERRAME, registrado_por=usuario)
    Novedad.objects.create(movimiento=mov, tipo_novedad=TipoNovedad.OTRA, registrado_por=usuario)
    api_client.force_authenticate(user=usuario)

    resp = api_client.get(reverse("api-novedad-list"), {"tipo_novedad": TipoNovedad.DERRAME})
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["tipo_novedad"] == TipoNovedad.DERRAME
