from rest_framework import generics
from .models import Encomienda, Cliente
from .serializers import EncomiendaSerializer


class EncomiendaListCreateView(generics.ListCreateAPIView):
    """Vista para listar y crear encomiendas (Corregido a APIView)"""
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaSerializer


class ClienteListView(generics.ListAPIView):
    """Vista para listar clientes"""
    queryset = Cliente.objects.all()
    # Nota: Si luego creas ClienteSerializer, cámbialo aquí.
    # Por ahora usamos EncomiendaSerializer para evitar errores de importación.
    serializer_class = EncomiendaSerializer
