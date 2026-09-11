from rest_framework import status
from rest_framework.response import Response


def form_errors_response(form, http_status=status.HTTP_400_BAD_REQUEST):
    """Convierte form.errors (ErrorDict de Django) al formato convencional de
    DRF: {campo: [mensajes]}, con __all__ renombrado a non_field_errors.
    Único punto de conversión para todas las vistas que reutilizan un Form
    existente en vez de un serializer."""

    errores = {}
    for campo, lista in form.errors.items():
        clave = "non_field_errors" if campo == "__all__" else campo
        errores[clave] = list(lista)
    return Response(errores, status=http_status)
