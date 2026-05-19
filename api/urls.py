from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# Importaciones de tus vistas
from envios.viewsets import EncomiendaViewSet
from envios.api_auth import EncomiendaTokenView, LoginCookieView
from envios.api_views import EncomiendaListCreateView, ClienteListView

# 1. Definimos el Router
router = DefaultRouter()
router.register(r'encomiendas', EncomiendaViewSet, basename='encomienda')

# 2. Definimos las rutas de Autenticación con el prefijo "auth"
# Esto generará: api/v1/auth/token/ , etc.
auth_patterns = [
    path('token/', EncomiendaTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login-cookie/', LoginCookieView.as_view(), name='api_login_cookie'),
]

# 3. Rutas de la versión 1
api_v1_patterns = [
    path('auth/', include(auth_patterns)), # <--- AQUÍ agregamos el prefijo auth
    path('', include(router.urls)),
    path('lista-encomiendas/', EncomiendaListCreateView.as_view(), name='api_encomienda_list'),
    path('clientes/', ClienteListView.as_view(), name='api_cliente_list'),
]

# 4. Rutas de la versión 2
api_v2_patterns = [
    path('auth/', include(auth_patterns)), # También disponible en v2
    path('', include(router.urls)),
]

# 5. URLPatterns Finales
urlpatterns = [
    # Rutas para Versionado
    path('v1/', include((api_v1_patterns, 'v1'))),
    path('v2/', include((api_v2_patterns, 'v2'))),
    
    # Mantener rutas globales (opcional)
    path('auth/', include(auth_patterns)),
    path('', include(router.urls)),
]