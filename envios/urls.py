from django.urls import path

from . import views
from . import views_cbv


urlpatterns = [

    path(
        '',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'encomiendas/',
        views_cbv.EncomiendaListView.as_view(),
        name='encomienda_lista'
    ),

    path(
        'encomiendas/nueva/',
        views_cbv.EncomiendaCreateView.as_view(),
        name='encomienda_crear'
    ),

    path(
        'encomiendas/<int:pk>/',
        views_cbv.EncomiendaDetailView.as_view(),
        name='encomienda_detalle'
    ),

    path(
        'encomiendas/<int:pk>/estado/',
        views.encomienda_cambiar_estado,
        name='encomienda_cambiar_estado'
    ),

    path(
        'encomiendas/<int:pk>/editar/',
        views.encomienda_editar,
        name='encomienda_editar'
    ),

    path(
        'encomiendas/buscar/<str:codigo>/',
        views.encomienda_por_codigo,
        name='buscar_por_codigo'
    ),

    path(
        'api/encomiendas/<uuid:uuid>/',
        views.encomienda_api,
        name='encomienda_api'
    ),
]

# Convertidores disponibles
# <int:nombre> → entero positivo
# <str:nombre> → cualquier texto (sin /)
# <slug:nombre> → letras, números, guiones y guiones bajos
# <uuid:nombre> → UUID formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# <path:nombre> → texto incluyendo /