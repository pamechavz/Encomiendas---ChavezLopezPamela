from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics
from django.http import Http404
from envios.models import Encomienda
from .serializers import EncomiendaSerializer, EncomiendaDetailSerializer
from rest_framework import viewsets


# ==========================================================
# 1. FBV - VISTAS BASADAS EN FUNCIONES (Punto 3 del Entregable)
# ==========================================================

@api_view(['GET', 'POST'])
def encomienda_list_create_fbv(request):
    if request.method == 'GET':
        encomiendas = Encomienda.objects.all()
        serializer = EncomiendaSerializer(encomiendas, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = EncomiendaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def encomienda_detail_fbv(request, pk):
    try:
        encomienda = Encomienda.objects.get(pk=pk)
    except Encomienda.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EncomiendaDetailSerializer(encomienda)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = EncomiendaDetailSerializer(encomienda, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        encomienda.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 2. CBV - VISTAS BASADAS EN CLASES (Punto 4 del Entregable)
# ==========================================================

class EncomiendaListAPIView(APIView):
    def get(self, request, format=None):
        encomiendas = Encomienda.objects.all()
        serializer = EncomiendaSerializer(encomiendas, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = EncomiendaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EncomiendaDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Encomienda.objects.get(pk=pk)
        except Encomienda.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        encomienda = self.get_object(pk)
        serializer = EncomiendaDetailSerializer(encomienda)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        encomienda = self.get_object(pk)
        serializer = EncomiendaDetailSerializer(encomienda, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        encomienda = self.get_object(pk)
        encomienda.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 3. MIXINS (Punto 5 del Entregable)
# ==========================================================

class EncomiendaListMixinView(mixins.ListModelMixin, 
                             mixins.CreateModelMixin, 
                             generics.GenericAPIView):
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

# Agrégalo debajo de tu EncomiendaListMixinView
class EncomiendaDetailMixinView(mixins.RetrieveModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.DestroyModelMixin,
                               generics.GenericAPIView):
    queryset = Encomienda.objects.all()
    # Usamos el Detail para que al consultar uno solo, se vea toda la info
    serializer_class = EncomiendaDetailSerializer 

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
# ==========================================================
# 4. GENERIC VIEWS (Punto 6 del Entregable)
# ==========================================================

class EncomiendaListCreateGenericView(generics.ListCreateAPIView):
    """
    Esta es la forma más corta de hacer lo mismo que los Mixins.
    """
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaSerializer

class EncomiendaRetrieveUpdateDestroyGenericView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaDetailSerializer



# ==========================================================
# 5. VIEWSETS (Punto 7 del Entregable Final)
# ==========================================================

class EncomiendaViewSet(viewsets.ModelViewSet):
    """
    Un solo ViewSet para todas las operaciones CRUD.
    Automatiza: list, create, retrieve, update, destroy.
    """
    queryset = Encomienda.objects.all()

    def get_serializer_class(self):
        """
        Punto 2 del entregable: Diferenciar entre lista y detalle.
        Si la acción es 'retrieve' (ver uno solo), usamos el DetailSerializer.
        """
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer