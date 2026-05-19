import django_filters
from envios.models import Encomienda

class EncomiendaFilter(django_filters.FilterSet):
    costo_min = django_filters.NumberFilter(field_name="costo_envio", lookup_expr='gte')
    costo_max = django_filters.NumberFilter(field_name="costo_envio", lookup_expr='lte')
    fecha_desde = django_filters.DateFilter(field_name="fecha_registro", lookup_expr='gte')
    fecha_hasta = django_filters.DateFilter(field_name="fecha_registro", lookup_expr='lte')

    class Meta:
        model = Encomienda
        fields = ['estado', 'remitente', 'destinatario', 'ruta', 'empleado_registro']