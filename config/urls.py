from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("acceso/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/", include("config.api_urls")),
    path("", include("ropa.urls")),
    path("", include("residuos.urls")),
    path("", include("movimientos.urls")),
    path("", include("reportes.urls")),
    path("", include("core.urls")),
]
