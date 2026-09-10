from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def panel_principal(request):
    """Pantalla 2 del sistema. En la etapa 5 se le agregan los accesos de
    registro y el listado de movimientos del día."""
    return render(request, "core/panel_principal.html")
