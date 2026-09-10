import pytest
from django.contrib.auth import get_user_model

from core.models import AreaServicio, Sede

Usuario = get_user_model()


@pytest.fixture
def usuario(db):
    return Usuario.objects.create_user(
        username="operario", password="clave-de-prueba", rol=Usuario.Rol.USUARIO,
    )


@pytest.fixture
def sede(db):
    return Sede.objects.create(nombre="Clínica")


@pytest.fixture
def area(db, sede):
    return AreaServicio.objects.create(sede=sede, nombre="Hemodinamia")


@pytest.fixture
def crear_movimiento(sede, area, usuario):
    """Fábrica de movimientos para las pruebas. La jornada NO se pasa: la
    calcula el modelo al guardar."""
    from movimientos.models import Movimiento

    def _crear(*, tipo, fecha, hora, **kwargs):
        params = {
            "tipo_movimiento": tipo,
            "fecha": fecha,
            "hora": hora,
            "sede": kwargs.pop("sede", sede),
            "area_origen": kwargs.pop("area_origen", area),
            "creado_por": kwargs.pop("creado_por", usuario),
        }
        params.update(kwargs)
        return Movimiento.objects.create(**params)

    return _crear
