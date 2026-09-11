from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Respaldo diario de la base de datos con retención (RNF-15)."

    def handle(self, *args, **options):
        inicio = timezone.now()
        self.stdout.write(f"Respaldo iniciado: {inicio:%Y-%m-%d %H:%M:%S}")
        call_command("dbbackup", "--clean", "--noinput", verbosity=1)
        self.stdout.write(self.style.SUCCESS("Respaldo completado."))
