import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
# Importamos las nuevas
from .factories import UserFactory, EncomiendaFactory, ClienteFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def encomienda_factory():
    return EncomiendaFactory


@pytest.fixture
def cliente_factory():
    return ClienteFactory


@pytest.fixture
def auth_client(db, user_factory):
    """Fixture para obtener un cliente autenticado fácilmente"""
    user = user_factory.create()
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client
