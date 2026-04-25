from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoEnvio, EstadoGeneral
import uuid
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from .querysets import EncomiendaQuerySet

class Encomienda(models.Model):
    objects = EncomiendaQuerySet.as_manager()  

    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField()
    peso_kg = models.DecimalField(max_digits=8, decimal_places=2)
    volumen_cm3 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    remitente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT,
        related_name='envios_como_remitente',
        null=True, blank=True
    )

    destinatario = models.ForeignKey(
        Cliente, on_delete=models.PROTECT,
        related_name='envios_como_destinatario',
        null=True, blank=True
    )

    ruta = models.ForeignKey(
        Ruta, on_delete=models.PROTECT,
        related_name='encomiendas',
        null=True, blank=True
    )

    empleado_registro = models.ForeignKey(
        'envios.Empleado', on_delete=models.PROTECT,
        related_name='encomiendas_registradas',
        null=True, blank=True
    )

    estado = models.CharField(
        max_length=2,
        choices=EstadoEnvio.choices,
        default=EstadoEnvio.PENDIENTE
    )

    costo_envio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_entrega_est = models.DateField(null=True, blank=True)
    fecha_entrega_real = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.codigo} [{self.get_estado_display()}]'

   

    @property
    def esta_entregada(self):
        return self.estado == EstadoEnvio.ENTREGADO

    @property
    def esta_en_transito(self):
        return self.estado == EstadoEnvio.EN_TRANSITO

    @property
    def dias_en_transito(self):
        if not self.fecha_registro:
            return 0
        delta = timezone.now().date() - self.fecha_registro.date()
        return delta.days

    @property
    def tiene_retraso(self):
        if not self.fecha_entrega_est or self.esta_entregada:
            return False
        return timezone.now().date() > self.fecha_entrega_est

    @property
    def descripcion_corta(self):
        if not self.descripcion:
            return ""
        return self.descripcion[:50] + '...' if len(self.descripcion) > 50 else self.descripcion



    def cambiar_estado(self, nuevo_estado, empleado, observacion=''):
        if nuevo_estado == self.estado:
            raise ValueError(
                f'La encomienda ya se encuentra en estado {self.get_estado_display()}'
            )

        estado_anterior = self.estado
        self.estado = nuevo_estado

        if nuevo_estado == EstadoEnvio.ENTREGADO:
            self.fecha_entrega_real = timezone.now().date()

        self.save()

        from envios.models import HistorialEstado

        HistorialEstado.objects.create(
            encomienda=self,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            empleado=empleado,
            observacion=observacion
        )

        return self

    def calcular_costo(self):
        PRECIO_POR_KG_EXTRA = Decimal('2.50')
        PESO_BASE = Decimal('5.0')

        if not self.ruta:
            return Decimal('0.00')

        costo = self.ruta.precio_base

        if self.peso_kg > PESO_BASE:
            costo += (self.peso_kg - PESO_BASE) * PRECIO_POR_KG_EXTRA

        return round(costo, 2)

    @classmethod
    def crear_con_costo_calculado(
        cls,
        remitente,
        destinatario,
        ruta,
        empleado,
        descripcion,
        peso_kg,
        **kwargs
    ):
        """
        Crea una encomienda con código automático y costo calculado
        """

        # Código único
        codigo = f'ENC-{timezone.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:6].upper()}'

        # Fecha estimada según la ruta
        fecha_estimada = timezone.now().date() + timedelta(days=ruta.dias_entrega)

        # Crear objeto sin guardar aún
        encomienda = cls(
            codigo=codigo,
            descripcion=descripcion,
            peso_kg=peso_kg,
            remitente=remitente,
            destinatario=destinatario,
            ruta=ruta,
            empleado_registro=empleado,
            fecha_entrega_est=fecha_estimada,
            **kwargs
        )

        # Calcular costo automáticamente
        encomienda.costo_envio = encomienda.calcular_costo()

        # Guardar (esto dispara clean() también)
        encomienda.save()

        return encomienda
    def clean(self):
        errors = {}

        if self.remitente_id and self.destinatario_id:
            if self.remitente_id == self.destinatario_id:
                errors['destinatario'] = ValidationError(
                    'El destinatario no puede ser el mismo que el remitente.'
                )

        if self.fecha_entrega_est:
            if self.fecha_entrega_est < timezone.now().date():
                errors['fecha_entrega_est'] = ValidationError(
                    'La fecha de entrega estimada no puede ser en el pasado.'
                )

        if self.fecha_entrega_est and self.fecha_entrega_real:
            if self.fecha_entrega_real < self.fecha_entrega_est:
                errors['fecha_entrega_real'] = ValidationError(
                    'La fecha de entrega real no puede ser antes de la estimada.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'encomiendas'
        verbose_name = 'Encomienda'
        verbose_name_plural = 'Encomiendas'
        ordering = ['-fecha_registro']
class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=15, unique=True)
    cargo = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
    
class HistorialEstado(models.Model):
    encomienda = models.ForeignKey(
        Encomienda,
        on_delete=models.CASCADE,
        related_name='historial'   
    )
    estado_anterior = models.CharField(max_length=2)
    estado_nuevo = models.CharField(max_length=2)
    empleado = models.ForeignKey('Empleado', on_delete=models.PROTECT)
    observacion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)