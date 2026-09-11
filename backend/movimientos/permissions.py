from rest_framework.permissions import BasePermission

from .services import motivo_no_editable


class PuedeEditarMovimiento(BasePermission):
    """Reutiliza motivo_no_editable (RF-041, 6.9) tal cual: no reimplementa
    la ventana de 60 minutos ni la regla de dueño. El motivo en español que
    ya devuelve el servicio queda disponible como detail del 403."""

    def has_object_permission(self, request, view, obj):
        motivo = motivo_no_editable(request.user, obj)
        if motivo:
            self.message = motivo
            return False
        return True
