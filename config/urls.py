"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from api.views import EncomiendaTokenView

def logout_view(request):
    auth_logout(request)
    return redirect('login')

# Personalizar título del Admin
admin.site.site_header = 'Sistema de Gestión de Encomiendas'
admin.site.site_title = 'Encomiendas Admin'
admin.site.index_title = 'Panel de Administración'

urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    # JWT Token URLs
    path(
        'api/v1/auth/token/',
        EncomiendaTokenView.as_view(),
        name='token_obtain'
    ),
    path(
        'api/v1/auth/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path(
        'api/v1/auth/token/blacklist/',
        TokenBlacklistView.as_view(),
        name='token_blacklist'
    ),

    # Documentacion
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger'
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),

    # API REST con versionado dinamico
    # <version> captura 'v1' o 'v2' de la URL
    path(
        'api/<version>/',
        include('api.urls')
    ),

    path(
        '',
        include('envios.urls')
    ),

    path(
        'accounts/login/',
        LoginView.as_view(template_name='accounts/login.html'),
        name='login'
    ),

    path(
        'accounts/logout/',
        logout_view,
        name='logout'
    ),

    path(
        'accounts/',
        include('django.contrib.auth.urls')
    ),
]

# En DEBUG=True, Django sirve los archivos estáticos automáticamente

if settings.DEBUG:
    urlpatterns += [
        path('silk/', include('silk.urls', namespace='silk')),
    ]

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )