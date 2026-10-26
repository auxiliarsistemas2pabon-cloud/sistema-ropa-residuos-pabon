import logging
import re
import shutil
import socket
from pathlib import Path

from dbbackup.storage import get_storage
from django.conf import settings
from django.core.mail import send_mail
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger(__name__)

# Nombre que da DBBACKUP_FILENAME_TEMPLATE: «20261026-200500-clinica_pabon...».
# Solo esos archivos se podan en la carpeta externa, nunca otros que estén ahí.
_NOMBRE_RESPALDO = re.compile(r"^\d{8}-\d{6}-")


class Command(BaseCommand):
    help = (
        "Respaldo diario de la base de datos con retención (RNF-15), cifrado, "
        "copia fuera del servidor y aviso por correo si falla (protocolo de seguridad, A5)."
    )

    def handle(self, *args, **options):
        inicio = timezone.localtime()
        self.stdout.write(f"Respaldo iniciado: {inicio:%Y-%m-%d %H:%M:%S}")
        try:
            argumentos = ["--clean", "--noinput"]
            if settings.RESPALDO_GPG_DESTINATARIO:
                self._importar_llave_publica()
                argumentos.append("--encrypt")
            call_command("dbbackup", *argumentos, verbosity=1)
            if settings.RESPALDO_COPIA_EXTERNA_DIR:
                copia = self._copiar_fuera_del_servidor()
                self.stdout.write(f"Copia fuera del servidor: {copia}")
        except Exception as error:
            self._avisar_fallo(inicio, error)
            raise CommandError(f"El respaldo falló: {error}") from error
        self.stdout.write(self.style.SUCCESS("Respaldo completado."))

    def _importar_llave_publica(self):
        """dbbackup cifra con la llave que esté en el llavero de GPG; se importa
        en cada corrida (no pasa nada si ya estaba) para que un contenedor
        recién creado no respalde sin cifrar."""
        if not settings.RESPALDO_GPG_LLAVE_PUBLICA:
            return
        import gnupg

        resultado = gnupg.GPG().import_keys_file(settings.RESPALDO_GPG_LLAVE_PUBLICA)
        if not resultado.count:
            raise CommandError(f"No se pudo importar la llave pública {settings.RESPALDO_GPG_LLAVE_PUBLICA}.")

    def _copiar_fuera_del_servidor(self):
        carpeta = Path(settings.RESPALDO_COPIA_EXTERNA_DIR)
        # Sin crearla: si el disco externo no está montado, crearla escribiría
        # la "copia externa" dentro del mismo servidor sin que nadie lo note.
        if not carpeta.is_dir():
            raise CommandError(f"La carpeta de la copia externa no existe o no está montada: {carpeta}")
        almacenamiento = get_storage()
        nombre = almacenamiento.get_latest_backup(content_type="db")
        destino = carpeta / Path(nombre).name
        with almacenamiento.read_file(nombre) as origen, open(destino, "wb") as salida:
            shutil.copyfileobj(origen, salida)
        esperado = almacenamiento.storage.size(nombre)
        if destino.stat().st_size != esperado:
            raise CommandError(f"La copia externa quedó incompleta: {destino.stat().st_size} de {esperado} bytes.")
        self._podar_copias_externas(carpeta)
        return destino

    def _podar_copias_externas(self, carpeta):
        """Conserva las últimas DBBACKUP_CLEANUP_KEEP copias y, además, la más
        reciente de cada uno de los últimos RESPALDO_MESES_CONSERVADOS meses:
        sirve si una alteración de datos se descubre tarde."""
        # El nombre empieza por la fecha y hora: ordenar por nombre es ordenar en el tiempo.
        archivos = sorted(p for p in carpeta.iterdir() if p.is_file() and _NOMBRE_RESPALDO.match(p.name))
        conservar = set(archivos[-settings.DBBACKUP_CLEANUP_KEEP:])
        ultimo_del_mes = {}
        for archivo in archivos:
            ultimo_del_mes[archivo.name[:6]] = archivo
        for mes in sorted(ultimo_del_mes)[-settings.RESPALDO_MESES_CONSERVADOS:]:
            conservar.add(ultimo_del_mes[mes])
        for archivo in archivos:
            if archivo not in conservar:
                archivo.unlink()

    def _avisar_fallo(self, inicio, error):
        logger.exception("El respaldo de la base de datos falló")
        if not settings.RESPALDO_AVISO_CORREOS:
            return
        try:
            send_mail(
                "[Clínica Pabón] El respaldo de la base de datos falló",
                f"Servidor: {socket.gethostname()}\n"
                f"Inicio: {inicio:%Y-%m-%d %H:%M:%S}\n"
                f"Error: {error}\n\n"
                "Revisar el servicio «respaldo» (docker compose logs respaldo) y la sección 4 de "
                "DESPLIEGUE.md. Dos días seguidos sin respaldo es un incidente de severidad media "
                "según los protocolos de seguridad.",
                None,
                settings.RESPALDO_AVISO_CORREOS,
            )
        except Exception:
            # El fallo original es lo importante: que no lo tape el del correo.
            logger.exception("Tampoco se pudo enviar el aviso por correo del respaldo fallido")
