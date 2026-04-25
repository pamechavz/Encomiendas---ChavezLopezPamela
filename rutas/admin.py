from django.contrib import admin
from .models import Ruta

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('id',)  