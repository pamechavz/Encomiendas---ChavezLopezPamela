from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from django.utils import timezone
from django.core.cache import cache  # Importante para el Paso 6 (Pág. 142)
from drf_spectacular.utils import extend_schema, extend_schema_view

# --- Importaciones de la Aplicación ---
from .models import Encomienda, Empleado
from .serializers import EncomiendaSerializer, EncomiendaDetailSerializer, EncomiendaV2Serializer
from config.choices import EstadoEnvio
from .throttles import EmpleadoRateThrottle, CambioEstadoThrottle
from .exceptions import EstadoInvalidoError, EncomiendaYaEntregadaError

# --- Filtros ---
class EncomiendaFilter(django_filters.FilterSet):
    costo_min = django_filters.NumberFilter(field_name="costo_envio", lookup_expr='gte')
    costo_max = django_filters.NumberFilter(field_name="costo_envio", lookup_expr='lte')
    fecha_desde = django_filters.DateFilter(field_name="fecha_registro", lookup_expr='gte')
    fecha_hasta = django_filters.DateFilter(field_name="fecha_registro", lookup_expr='lte')

    class Meta:
        model = Encomienda
        fields = ['estado', 'remitente', 'destinatario', 'ruta', 'empleado_registro']

# --- ViewSet Principal ---
@extend_schema_view(
    list=extend_schema(summary="Listar encomiendas", tags=['Encomiendas']),
    retrieve=extend_schema(summary="Detalle de encomienda", tags=['Encomiendas']),
    create=extend_schema(summary="Crear encomienda", tags=['Encomiendas']),
    update=extend_schema(summary="Actualizar encomienda", tags=['Encomiendas']),
    partial_update=extend_schema(summary="Actualizar parcialmente", tags=['Encomiendas']),
    destroy=extend_schema(summary="Eliminar encomienda", tags=['Encomiendas']),
)
class EncomiendaViewSet(viewsets.ModelViewSet):
    queryset = Encomienda.objects.all().select_related(
        'remitente', 'destinatario', 'ruta', 'empleado_registro'
    )

    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmpleadoRateThrottle]

    def get_throttles(self):
        if self.action == 'cambiar_estado':
            return [CambioEstadoThrottle()]
        return super().get_throttles()

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EncomiendaFilter
    search_fields = ['codigo', 'descripcion', 'remitente__nombre', 'destinatario__nombre']
    ordering_fields = ['fecha_registro', 'costo_envio', 'peso_kg', 'id']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        version = getattr(self.request, 'version', 'v1')
        if version == 'v2':
            return EncomiendaV2Serializer
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    def _get_empleado_autenticado(self):
        empleado = Empleado.objects.filter(nombre__icontains=self.request.user.username).first()
        return empleado if empleado else Empleado.objects.first()

    # --- Acciones de Cambio de Estado con Invalidación de Caché ---
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None, *args, **kwargs):
        encomienda = self.get_object()

        if encomienda.estado == EstadoEnvio.ENTREGADO:
            raise EncomiendaYaEntregadaError()

        nuevo_estado = request.data.get('estado')
        empleado_id = request.data.get('empleado_id')
        observacion = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response({'error': 'Falta parámetro: estado'}, status=400)

        try:
            empleado = Empleado.objects.get(id=empleado_id) if empleado_id else self._get_empleado_autenticado()
            
            # Ejecutar el cambio en el modelo
            encomienda.cambiar_estado(nuevo_estado, empleado, observacion)

            # --- IMPLEMENTACIÓN PÁGINA 142: Invalidar caché de estadísticas ---
            cache.delete_many([
                f'estadisticas_empleado_{request.user.id}',
                f'encomienda_detalle_{pk}',
            ])

            return Response({
                'status': 'Estado actualizado correctamente',
                'nuevo_estado': encomienda.get_estado_display()
            })
        except Empleado.DoesNotExist:
            return Response({'error': 'El empleado no existe'}, status=404)
        except ValueError as e:
            raise EstadoInvalidoError(detail=str(e))

    # --- Otras Acciones ---
    @action(detail=False, methods=['get'])
    def pendientes(self, request, *args, **kwargs):
        pendientes = self.get_queryset().filter(estado=EstadoEnvio.PENDIENTE)
        page = self.paginate_queryset(pendientes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(pendientes, many=True).data)

    def perform_create(self, serializer):
        empleado = self._get_empleado_autenticado()
        serializer.save(empleado_registro=empleado)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if hasattr(request, 'version') and request.version:
            response['X-API-Version'] = request.version
        return response