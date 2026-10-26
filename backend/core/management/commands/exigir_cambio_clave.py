from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Exige cambiar la contraseña en el próximo ingreso (protocolo de seguridad, A4). "
        "Sirve para las cuentas creadas antes de esta regla, cuya clave conoce quien la asignó."
    )

    def add_arguments(self, parser):
        parser.add_argument("usuarios", nargs="*", help="Nombres de usuario (username).")
        parser.add_argument(
            "--todos", action="store_true",
            help="Todas las cuentas activas, menos los superusuarios (su clave la custodia Sistemas).",
        )

    def handle(self, *args, usuarios, todos, **options):
        Usuario = get_user_model()
        if todos == bool(usuarios):
            raise CommandError("Indica nombres de usuario o --todos, no ambos.")
        if todos:
            cuentas = Usuario.objects.filter(activo=True, is_superuser=False)
        else:
            cuentas = Usuario.objects.filter(username__in=usuarios)
            faltan = set(usuarios) - set(cuentas.values_list("username", flat=True))
            if faltan:
                raise CommandError(f"No existen: {', '.join(sorted(faltan))}.")
        marcadas = 0
        for cuenta in cuentas:
            # save() y no update(): el cambio queda en el historial del usuario.
            cuenta.debe_cambiar_clave = True
            cuenta.save(update_fields=["debe_cambiar_clave"])
            marcadas += 1
        self.stdout.write(self.style.SUCCESS(f"{marcadas} cuenta(s) deberán cambiar la contraseña al entrar."))
