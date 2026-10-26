from django.conf import settings
from django.core.checks import Tags, Warning, register


@register(Tags.security, deploy=True)
def respaldos_protegidos(app_configs, **kwargs):
    """`manage.py check --deploy` avisa mientras los respaldos no cumplan el
    protocolo de seguridad (A5). Ver DESPLIEGUE.md, sección 4."""
    avisos = []
    if not settings.RESPALDO_GPG_DESTINATARIO:
        avisos.append(Warning(
            "Los respaldos de la base de datos se guardan sin cifrar.",
            hint="Define RESPALDO_GPG_DESTINATARIO y RESPALDO_GPG_LLAVE_PUBLICA en .env.",
            id="core.W001",
        ))
    if not settings.RESPALDO_COPIA_EXTERNA_DIR:
        avisos.append(Warning(
            "Los respaldos no salen del servidor: un daño del disco se lleva la base y sus copias.",
            hint="Monta un disco externo o carpeta de red y define RESPALDO_COPIA_EXTERNA_DIR en .env.",
            id="core.W002",
        ))
    if not settings.RESPALDO_AVISO_CORREOS:
        avisos.append(Warning(
            "Nadie recibe aviso si un respaldo falla.",
            hint="Define RESPALDO_AVISO_CORREOS y los datos de EMAIL_* en .env.",
            id="core.W003",
        ))
    return avisos
