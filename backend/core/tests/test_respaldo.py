from unittest import mock

import pytest
from django.conf import settings
from django.core import mail
from django.core.checks import run_checks
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError

RESPALDO = "core.management.commands.respaldo_diario"


def test_comando_respaldo_registrado():
    assert "respaldo_diario" in get_commands()


def test_dbbackup_configurado():
    assert "dbbackup" in settings.INSTALLED_APPS
    assert "dbbackup" in settings.STORAGES
    assert settings.DBBACKUP_CLEANUP_KEEP >= 30  # RNF-15: retención mínima 30 días


# --- Protocolo de seguridad, A5 ---------------------------------------------

class _AlmacenamientoFalso:
    """Lo mínimo de dbbackup.storage.Storage que usa el comando."""

    def __init__(self, carpeta, nombre, contenido=b"respaldo cifrado"):
        self.carpeta, self.nombre = carpeta, nombre
        (carpeta / nombre).write_bytes(contenido)
        self.storage = mock.Mock(size=lambda nombre: (carpeta / nombre).stat().st_size)

    def get_latest_backup(self, **kwargs):
        return self.nombre

    def read_file(self, nombre):
        return open(self.carpeta / nombre, "rb")


@pytest.fixture
def carpetas(tmp_path):
    local, externa = tmp_path / "local", tmp_path / "externa"
    local.mkdir()
    externa.mkdir()
    return local, externa


def test_cifra_si_hay_llave_configurada(settings):
    settings.RESPALDO_GPG_DESTINATARIO = "respaldos@clinica.example"
    settings.RESPALDO_GPG_LLAVE_PUBLICA = ""
    with mock.patch(f"{RESPALDO}.call_command") as dbbackup:
        call_command("respaldo_diario")
    assert "--encrypt" in dbbackup.call_args.args


def test_sin_llave_no_cifra(settings):
    settings.RESPALDO_GPG_DESTINATARIO = ""
    with mock.patch(f"{RESPALDO}.call_command") as dbbackup:
        call_command("respaldo_diario")
    assert "--encrypt" not in dbbackup.call_args.args


def test_copia_el_ultimo_respaldo_fuera_del_servidor(settings, carpetas):
    local, externa = carpetas
    settings.RESPALDO_COPIA_EXTERNA_DIR = str(externa)
    almacen = _AlmacenamientoFalso(local, "20261026-200500-clinica_pabon.psql.bin.gpg")
    with mock.patch(f"{RESPALDO}.call_command"), mock.patch(f"{RESPALDO}.get_storage", return_value=almacen):
        call_command("respaldo_diario")
    assert (externa / almacen.nombre).read_bytes() == b"respaldo cifrado"


def test_en_la_carpeta_externa_conserva_los_recientes_y_uno_por_mes(settings, carpetas):
    local, externa = carpetas
    settings.RESPALDO_COPIA_EXTERNA_DIR = str(externa)
    settings.DBBACKUP_CLEANUP_KEEP = 3
    settings.RESPALDO_MESES_CONSERVADOS = 3
    for nombre in [
        "20260715-200500-clinica_pabon.psql.bin",  # mes fuera de los 3 conservados
        "20260830-200500-clinica_pabon.psql.bin",
        "20260831-200500-clinica_pabon.psql.bin",  # el último de agosto
        "20260929-200500-clinica_pabon.psql.bin",
        "20260930-200500-clinica_pabon.psql.bin",
        "notas-del-nas.txt",  # ajeno: nunca se toca
    ]:
        (externa / nombre).write_bytes(b"x")
    almacen = _AlmacenamientoFalso(local, "20261001-200500-clinica_pabon.psql.bin")
    with mock.patch(f"{RESPALDO}.call_command"), mock.patch(f"{RESPALDO}.get_storage", return_value=almacen):
        call_command("respaldo_diario")
    assert sorted(p.name for p in externa.iterdir()) == [
        "20260831-200500-clinica_pabon.psql.bin",
        "20260929-200500-clinica_pabon.psql.bin",
        "20260930-200500-clinica_pabon.psql.bin",
        "20261001-200500-clinica_pabon.psql.bin",
        "notas-del-nas.txt",
    ]


def test_si_el_disco_externo_no_esta_montado_falla_y_avisa(settings, tmp_path):
    settings.RESPALDO_COPIA_EXTERNA_DIR = str(tmp_path / "no-montado")
    settings.RESPALDO_AVISO_CORREOS = ["sistemas@clinica.example"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    with mock.patch(f"{RESPALDO}.call_command"), pytest.raises(CommandError, match="no está montada"):
        call_command("respaldo_diario")
    assert not (tmp_path / "no-montado").exists()
    assert len(mail.outbox) == 1
    assert "falló" in mail.outbox[0].subject
    assert mail.outbox[0].to == ["sistemas@clinica.example"]


def test_si_dbbackup_falla_avisa_por_correo(settings):
    settings.RESPALDO_AVISO_CORREOS = ["sistemas@clinica.example"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    with mock.patch(f"{RESPALDO}.call_command", side_effect=RuntimeError("pg_dump: conexión rechazada")):
        with pytest.raises(CommandError):
            call_command("respaldo_diario")
    assert "pg_dump: conexión rechazada" in mail.outbox[0].body


def test_check_deploy_avisa_si_los_respaldos_no_estan_protegidos(settings):
    settings.RESPALDO_GPG_DESTINATARIO = ""
    settings.RESPALDO_COPIA_EXTERNA_DIR = ""
    settings.RESPALDO_AVISO_CORREOS = []
    ids = {aviso.id for aviso in run_checks(include_deployment_checks=True)}
    assert {"core.W001", "core.W002", "core.W003"} <= ids
