from rest_framework import serializers
from django.utils import timezone
from .models import Encomienda, Cliente, Empleado
from config.choices import EstadoEnvio

def validate_codigo_formato(value):
    if not value.startswith('ENC-'):
        raise serializers.ValidationError("El código debe iniciar con el prefijo 'ENC-'.")
    return value

class EncomiendaSerializer(serializers.ModelSerializer):
    codigo = serializers.CharField(validators=[validate_codigo_formato])

    class Meta:
        model = Encomienda
        fields = '__all__'
        read_only_fields = ['fecha_registro', 'fecha_entrega_real']

    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor a 0 kg.")
        if value > 1000:
            raise serializers.ValidationError("No se aceptan encomiendas de más de 1000 kg.")
        return value

    def validate_costo_envio(self, value):
        if value < 5:
            raise serializers.ValidationError("El costo de envío mínimo es de 5.00.")
        return value

    def validate(self, data):
        remitente = data.get('remitente')
        destinatario = data.get('destinatario')
        if remitente and destinatario and remitente == destinatario:
            raise serializers.ValidationError({
                "destinatario": "El remitente y el destinatario no pueden ser la misma persona."
            })

        fecha_entrega_est = data.get('fecha_entrega_est')
        if fecha_entrega_est and fecha_entrega_est < timezone.now().date():
            raise serializers.ValidationError({
                "fecha_entrega_est": "La fecha de entrega estimada no puede ser anterior a hoy."
            })
        return data

class EncomiendaDetailSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.ReadOnlyField(source='remitente.nombre')
    destinatario_nombre = serializers.ReadOnlyField(source='destinatario.nombre')
    ruta_nombre = serializers.ReadOnlyField(source='ruta.nombre')
    empleado_nombre = serializers.ReadOnlyField(source='empleado_registro.nombre')
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente', 'remitente_nombre', 
            'destinatario', 'destinatario_nombre',
            'ruta', 'ruta_nombre',
            'estado', 'estado_display',
            'costo_envio', 'fecha_registro', 'fecha_entrega_est'
        ]

class EncomiendaV2Serializer(serializers.ModelSerializer):
    remitente_full = serializers.CharField(source='remitente.nombre', read_only=True)
    destinatario_full = serializers.CharField(source='destinatario.nombre', read_only=True)
    tipo_carga = serializers.SerializerMethodField()
    codigo = serializers.CharField(validators=[validate_codigo_formato])

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg', 
            'remitente_full', 'destinatario_full', 'tipo_carga',
            'estado', 'fecha_registro'
        ]
        read_only_fields = ['fecha_registro']

    def get_tipo_carga(self, obj):
        return "Pesada" if obj.peso_kg > 50 else "Ligera"

    def validate_peso_kg(self, value):
        if value <= 0 or value > 1000:
            raise serializers.ValidationError("Peso inválido para v2 (1-1000kg).")
        return value