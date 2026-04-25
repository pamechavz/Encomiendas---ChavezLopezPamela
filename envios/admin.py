from django.contrib import admin
from .models import Encomienda, Empleado, HistorialEstado

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'dni', 'cargo')


@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'peso_kg', 'estado')


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ('encomienda', 'estado_anterior', 'estado_nuevo', 'fecha')