# envios/views_cbv.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from .models import Encomienda, Empleado
from .forms import EncomiendaForm
from config.choices import EstadoEnvio

# --- Importaciones para la API ---
from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import EncomiendaSerializer

class EncomiendaListView(LoginRequiredMixin, ListView):
    model = Encomienda
    template_name = 'envios/lista.html'
    context_object_name = 'encomiendas'
    paginate_by = 15
    ordering = ['-fecha_registro']

    def get_queryset(self):
        # Aplicando optimización de la página 128
        qs = Encomienda.objects.con_relaciones()

        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        q = self.request.GET.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(codigo__icontains=q) |
                Q(remitente__apellidos__icontains=q) |
                Q(destinatario__apellidos__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = EstadoEnvio.choices
        ctx['estado_activo'] = self.request.GET.get('estado', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class EncomiendaDetailView(LoginRequiredMixin, DetailView):
    model = Encomienda
    template_name = 'envios/detalle.html'
    context_object_name = 'encomienda'

    def get_queryset(self):
        return Encomienda.objects.con_relaciones()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['historial'] = self.object.historial.select_related('empleado')
        return ctx


class EncomiendaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Encomienda
    form_class = EncomiendaForm
    template_name = 'envios/form.html'
    success_message = 'Encomienda %(codigo)s creada correctamente.'

    def get_success_url(self):
        return reverse_lazy('encomienda_detalle', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if not form.instance.costo_envio:
            form.instance.costo_envio = form.instance.calcular_costo() or 0.00
        
        empleado_disponible = Empleado.objects.first()
        if empleado_disponible:
            form.instance.empleado_registro = empleado_disponible
        return super().form_valid(form)


class EncomiendaUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Encomienda
    form_class = EncomiendaForm
    template_name = 'envios/form.html'
    success_message = 'Encomienda actualizada correctamente.'

    def get_success_url(self):
        return reverse_lazy('encomienda_detalle', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar'
        return ctx



class EncomiendaListAPIView(APIView):
    """
    Lista y crea encomiendas usando la lógica manual de APIView.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Solución de rendimiento con_relaciones() (Pág. 128)
        encomiendas = Encomienda.objects.con_relaciones().all()
        serializer = EncomiendaSerializer(encomiendas, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EncomiendaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class EncomiendaMixinAPIView(mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            generics.GenericAPIView):
    """
    Demuestra el uso de Mixins para comportamiento modular.
    """
    queryset = Encomienda.objects.con_relaciones()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class EncomiendaListCreateGeneric(generics.ListCreateAPIView):
    """
    Implementación final optimizada usando Generic Views.
    """
    queryset = Encomienda.objects.con_relaciones()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]


class EncomiendaDetailUpdateDestroyGeneric(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista genérica para operaciones de detalle y borrado.
    """
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]