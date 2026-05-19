from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from .models import Encomienda, Cliente, Empleado
from config.choices import EstadoEnvio

# --- Validadores Externos ---


def validate_codigo_formato(value):
    if not value.startswith('ENC-'):
        raise serializers.ValidationError(
            "El código debe iniciar con el prefijo 'ENC-'.")
    return value

# --- 6.13.5 EncomiendaBulkSerializer ---


class EncomiendaBulkSerializer(serializers.ListSerializer):
    """
    Serializer para operaciones masivas.
    Se activa automáticamente cuando se usa EncomiendaSerializer(many=True).
    """

    def create(self, validated_data):
        encomiendas = [
            Encomienda(**item) for item in validated_data
        ]
        return Encomienda.objects.bulk_create(encomiendas)

    def update(self, instances, validated_data):
        instance_map = {enc.id: enc for enc in instances}
        updated = []
        for item in validated_data:
            enc_id = item.pop('id', None)
            enc = instance_map.get(enc_id)
            if enc:
                for campo, valor in item.items():
                    setattr(enc, campo, valor)
                updated.append(enc)

        if updated:
            # Campos permitidos para actualización masiva
            Encomienda.objects.bulk_update(
                updated,
                ['estado', 'observaciones', 'costo_envio'],
            )
        return updated

# --- EncomiendaSerializer Principal ---


class EncomiendaSerializer(serializers.ModelSerializer):
    # Campos calculados definidos en el modelo o via ReadOnlyField
    esta_entregada = serializers.ReadOnlyField()
    tiene_retraso = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()

    # Validadores y campos especiales
    codigo = serializers.CharField(validators=[validate_codigo_formato])
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model = Encomienda
        fields = '__all__'
        read_only_fields = ['codigo', 'fecha_registro', 'fecha_entrega_real']
        # 6.13.5: Activa el bulk serializer
        list_serializer_class = EncomiendaBulkSerializer

    def get_estado_display(self, obj):
        return obj.get_estado_display()

    # --- 6.13.3 to_internal_value (Normalización) ---
    def to_internal_value(self, data):
        """ Limpia los datos antes de la validación """
        if hasattr(data, '_mutable'):
            data._mutable = True
        data = data.copy() if hasattr(data, 'copy') else dict(data)

        # 1. Normalizar código (Mayúsculas)
        if 'codigo' in data and data['codigo']:
            data['codigo'] = str(data['codigo']).upper().strip()

        # 2. Limpiar descripción
        if 'descripcion' in data and data['descripcion']:
            data['descripcion'] = str(data['descripcion']).strip()

        # 3. Normalizar decimales del costo
        if 'costo_envio' in data and data['costo_envio']:
            try:
                costo = Decimal(str(data['costo_envio']))
                data['costo_envio'] = str(
                    costo.quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP))
            except (ValueError, TypeError, Exception):
                pass

        return super().to_internal_value(data)

    # --- 6.13.1 to_representation (Personalización de Salida) ---
    def to_representation(self, instance):
        """ Modifica el JSON de salida """
        data = super().to_representation(instance)

        # 1. Datos de la ruta para conveniencia
        if instance.ruta_id:
            data['ruta_codigo'] = instance.ruta.codigo
            data['ruta_destino'] = instance.ruta.destino
            data['ruta_origen'] = instance.ruta.origen

        # 2. Formato de moneda
        data['costo_display'] = f'S/ {instance.costo_envio:.2f}'

        # 3. Seguridad: Ocultar campos a no-staff
        request = self.context.get('request')
        if request and not request.user.is_staff:
            data.pop('observaciones', None)
            data.pop('empleado_registro', None)

        # 4. Indicador visual de color
        colores = {
            'PE': 'gray',
            'TR': 'blue',
            'DE': 'orange',
            'EN': 'green',
            'DV': 'red',
        }
        data['estado_color'] = colores.get(instance.estado, 'gray')

        return data

    # --- Validaciones de Campo ---
    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor a 0 kg.")
        if value > 1000:
            raise serializers.ValidationError(
                "No se aceptan encomiendas de más de 1000 kg.")
        return value

    def validate_costo_envio(self, value):
        if value < 5:
            raise serializers.ValidationError(
                "El costo de envío mínimo es de 5.00.")
        return value

    # --- Validación de Objeto ---
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

# --- Otros Serializers ---


class EncomiendaDetailSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.ReadOnlyField(source='remitente.nombre')
    destinatario_nombre = serializers.ReadOnlyField(
        source='destinatario.nombre')
    ruta_nombre = serializers.ReadOnlyField(source='ruta.nombre')
    empleado_nombre = serializers.ReadOnlyField(
        source='empleado_registro.nombre')
    estado_display = serializers.CharField(
        source='get_estado_display', read_only=True)

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente', 'remitente_nombre',
            'destinatario', 'destinatario_nombre',
            'ruta', 'ruta_nombre',
            'estado', 'estado_display',
            'costo_envio', 'fecha_registro', 'fecha_entrega_est',
            # --- CAMPOS QUE FALTABAN ---
            'empleado_registro',  # El ID del empleado
            'empleado_nombre',   # El nombre que causaba el error
        ]
        read_only_fields = ['codigo', 'fecha_registro', 'empleado_registro']


class EncomiendaV2Serializer(serializers.ModelSerializer):
    remitente_full = serializers.CharField(
        source='remitente.nombre', read_only=True)
    destinatario_full = serializers.CharField(
        source='destinatario.nombre', read_only=True)
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
            raise serializers.ValidationError(
                "Peso inválido para v2 (1-1000kg).")
        return value
