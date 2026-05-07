# envios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST # <--- Importación corregida
from django.contrib import messages
from django.utils import timezone
from .models import Encomienda, Empleado
from config.choices import EstadoEnvio

@login_required
def dashboard(request):
    """Vista principal del sistema con estadísticas"""
    hoy = timezone.now().date()
    context = {
        'total_activas': Encomienda.objects.activas().count(),
        'en_transito': Encomienda.objects.en_transito().count(),
        'con_retraso': Encomienda.objects.con_retraso().count(),
        'entregadas_hoy': Encomienda.objects.filter(
            estado=EstadoEnvio.ENTREGADO, 
            fecha_entrega_real=hoy
        ).count(),
        'ultimas': Encomienda.objects.con_relaciones()[:5],
    }
    return render(request, 'envios/dashboard.html', context)

@login_required
@require_POST
def encomienda_cambiar_estado(request, pk):
    """Cambia el estado de una encomienda recibiendo datos por POST"""
    enc = get_object_or_404(Encomienda, pk=pk)
    nuevo_estado = request.POST.get('estado')
    observacion = request.POST.get('observacion', '')
    
    try:
        empleado = Empleado.objects.get(email=request.user.email)
        enc.cambiar_estado(nuevo_estado, empleado, observacion)
        messages.success(request, f'Estado actualizado a: {enc.get_estado_display()}')
    except ValueError as e:
        messages.error(request, str(e))
        
    return redirect('encomienda_detalle', pk=pk)