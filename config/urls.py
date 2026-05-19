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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularRedocView, 
    SpectacularSwaggerView
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Configuración del encabezado del Admin
admin.site.site_header = 'Sistema de Gestión de Encomiendas'
admin.site.site_title = 'Encomiendas Admin'
admin.site.index_title = 'Panel de Administración'

# 1. Definición de rutas base
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- DOCUMENTACIÓN ---
    path('docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # --- AUTENTICACIÓN JWT ---
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --- API VERSIONADA ---
    # re_path para limitar la versión a v1 o v2 y evitar rutas infinitas en Swagger
    re_path(r'^api/(?P<version>v1|v2)/', include('api.urls')),
    
    # Aplicación Web (Frontend local) - DEBE IR AL FINAL DE LAS RUTAS DINÁMICAS
    path('', include('envios.urls')),
]

# --- CONFIGURACIÓN PARA DESARROLLO (DEBUG) ---
if settings.DEBUG:
    # IMPORTANTE: Insertamos Silk al inicio de la lista para ganar prioridad
    # Esto evita que Nginx o el frontend intercepten la ruta /silk/
    urlpatterns = [
        path('silk/', include('silk.urls', namespace='silk')),
    ] + urlpatterns
    
    # Archivos Estáticos y Media
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)