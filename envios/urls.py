from django.urls import path
from . import views, views_cbv, views_auth

urlpatterns = [
    # Dashboard y FBV
    path('', views.dashboard, name='dashboard'),

    # Autenticación
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('perfil/', views_auth.perfil_view, name='perfil'),

    path('api/v1/cbv-manual/', views_cbv.EncomiendaListAPIView.as_view()),
    path('api/v1/cbv-mixins/', views_cbv.EncomiendaMixinAPIView.as_view()),
    path('api/v1/cbv-generic/', views_cbv.EncomiendaListCreateGeneric.as_view()),

    # Operaciones CRUD (CBV)
    path(
        'encomiendas/',
        views_cbv.EncomiendaListView.as_view(),
        name='encomienda_lista'),
    path(
        'encomiendas/<int:pk>/',
        views_cbv.EncomiendaDetailView.as_view(),
        name='encomienda_detalle'),
    path(
        'encomiendas/nueva/',
        views_cbv.EncomiendaCreateView.as_view(),
        name='encomienda_crear'),
    path(
        'encomiendas/<int:pk>/editar/',
        views_cbv.EncomiendaUpdateView.as_view(),
        name='encomienda_editar'),

    # Acciones específicas (FBV)
    path('encomiendas/<int:pk>/estado/',
         views.encomienda_cambiar_estado,
         name='encomienda_cambiar_estado'),
]
