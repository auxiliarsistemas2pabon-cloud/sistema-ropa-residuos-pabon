from django.conf import settings
from django.core.management import get_commands


def test_comando_respaldo_registrado():
    assert "respaldo_diario" in get_commands()


def test_dbbackup_configurado():
    assert "dbbackup" in settings.INSTALLED_APPS
    assert "dbbackup" in settings.STORAGES
    assert settings.DBBACKUP_CLEANUP_KEEP >= 30  # RNF-15: retención mínima 30 días
