# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from envios.viewsets import EncomiendaViewSet, RutaViewSet
from envios import api_views

# ── Router principal ─────────────────────────────────────────────
router = DefaultRouter()
router.register(
    'encomiendas',
    EncomiendaViewSet,
    basename='encomienda'
)
router.register(
    'rutas',
    RutaViewSet,
    basename='ruta'
)

# ── URLs de la API ───────────────────────────────────────────────
urlpatterns = [
    # URLs automáticas del ViewSet
    path('', include(router.urls)),

    # Endpoints adicionales
    path(
        'clientes/',
        api_views.ClienteListView.as_view()
    ),

]
