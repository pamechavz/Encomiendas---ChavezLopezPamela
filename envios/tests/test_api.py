import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from envios.models import Encomienda
from .factories import (
    UserFactory, ClienteFactory, RutaFactory,
    EmpleadoFactory, EncomiendaFactory
)

# Definimos la URL base como una constante para no repetir errores
BASE_URL = '/api/v1/encomiendas/'


@pytest.mark.django_db
class TestAutenticacion:
    """Pruebas de seguridad y acceso"""

    def test_sin_token_devuelve_401(self, api_client):
        url = BASE_URL
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_invalido_devuelve_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION='Bearer tokeninvalido')
        url = BASE_URL
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_con_token_valido_devuelve_200(self, auth_client):
        url = BASE_URL
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestListadoEncomiendas:
    """Pruebas de listado, filtros y búsqueda"""

    def setup_method(self):
        self.user = UserFactory()
        # Vinculamos empleado al usuario
        self.empleado = EmpleadoFactory(nombre=self.user.username)
        self.ruta = RutaFactory()
        self.cliente1 = ClienteFactory()
        self.cliente2 = ClienteFactory()

        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_lista_respuesta_paginada(self):
        EncomiendaFactory.create_batch(
            2,
            remitente=self.cliente1,
            destinatario=self.cliente2,
            ruta=self.ruta,
            empleado_registro=self.empleado)
        url = BASE_URL
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Verificamos estructura de paginación estándar de DRF
        assert 'results' in response.data
        assert len(response.data['results']) >= 2

    def test_filtro_por_estado(self):
        # Creamos registros con estados específicos
        enc_pe = EncomiendaFactory(
            estado='PE',
            ruta=self.ruta,
            empleado_registro=self.empleado)
        enc_tr = EncomiendaFactory(
            estado='TR',
            ruta=self.ruta,
            empleado_registro=self.empleado)

        url = f"{BASE_URL}?estado=PE"
        response = self.client.get(url)

        # Extraemos códigos de la respuesta
        codigos = [r['codigo'] for r in response.data['results']]
        assert enc_pe.codigo in codigos
        assert enc_tr.codigo not in codigos


@pytest.mark.django_db
class TestCrearEncomienda:
    """Pruebas de creación y validaciones de negocio"""

    def setup_method(self):
        self.user = UserFactory()
        self.empleado = EmpleadoFactory(nombre=self.user.username)
        self.cliente1 = ClienteFactory()
        self.cliente2 = ClienteFactory()
        self.ruta = RutaFactory(precio_base=Decimal('25.00'))

        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        self.data_valida = {
            'codigo': 'ENC-2026-TEST',
            'descripcion': 'Paquete de prueba',
            'peso_kg': '3.50',
            'costo_envio': '25.00',
            'remitente': self.cliente1.pk,
            'destinatario': self.cliente2.pk,
            'ruta': self.ruta.pk,
            'estado': 'PE'
        }

    def test_crear_exitoso_devuelve_201(self):
        url = BASE_URL
        response = self.client.post(url, self.data_valida, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['codigo'] == 'ENC-2026-TEST'
        assert Encomienda.objects.filter(codigo='ENC-2026-TEST').exists()

    def test_remitente_igual_destinatario_devuelve_400(self):
        # Caso de negocio: No puedes enviarte a ti mismo
        data = self.data_valida.copy()
        data['destinatario'] = self.cliente1.pk

        url = BASE_URL
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Verificamos que el error esté en el campo correcto o errores
        # generales
        assert 'destinatario' in response.data['detail'] or 'non_field_errors' in response.data['detail']

    def test_peso_negativo_devuelve_400(self):
        data = self.data_valida.copy()
        data['peso_kg'] = '-1.00'

        url = BASE_URL
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'peso_kg' in response.data['detail']
