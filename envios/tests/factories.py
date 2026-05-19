import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from envios.models import Encomienda, Cliente, Empleado
from rutas.models import Ruta
from decimal import Decimal


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Faker('user_name')
    email = factory.Faker('email')


class EmpleadoFactory(DjangoModelFactory):
    class Meta:
        model = Empleado
    nombre = factory.Faker('name')
    dni = factory.Sequence(lambda n: f"DNI-{1000+n}")
    cargo = 'Operador'


class ClienteFactory(DjangoModelFactory):
    class Meta:
        model = Cliente
    nro_doc = factory.Sequence(lambda n: f"DNI-{2000+n}")
    nombres = factory.Faker('first_name')
    apellidos = factory.Faker('last_name')
    email = factory.Faker('email')
    telefono = factory.Faker('numerify', text='9########')


class RutaFactory(DjangoModelFactory):
    class Meta:
        model = Ruta

    # Ajustado a tu modelos/rutas.py
    codigo = factory.Sequence(lambda n: f"RT-{n:03d}")
    origen = factory.Iterator(['Lima', 'Chiclayo', 'Trujillo', 'Piura'])
    destino = factory.Iterator(['Cusco', 'Arequipa', 'Ica', 'Tacna'])
    descripcion = factory.Faker('sentence')
    precio_base = Decimal('25.00')
    dias_entrega = 2
    estado = 1  # EstadoGeneral.ACTIVO suele ser 1


class EncomiendaFactory(DjangoModelFactory):
    class Meta:
        model = Encomienda

    codigo = factory.Sequence(lambda n: f"ENC-{3000+n}")
    descripcion = factory.Faker('sentence')
    peso_kg = Decimal('5.00')
    costo_envio = Decimal('25.00')
    remitente = factory.SubFactory(ClienteFactory)
    destinatario = factory.SubFactory(ClienteFactory)
    ruta = factory.SubFactory(RutaFactory)
    empleado_registro = factory.SubFactory(EmpleadoFactory)
    estado = 'PE'
