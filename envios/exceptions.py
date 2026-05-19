from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
import logging

# Configuración del logger para capturar errores internos
logger = logging.getLogger(__name__)

# --- 1. Excepciones Personalizadas de Negocio ---


class EstadoInvalidoError(APIException):
    """Error cuando la transición de estado no es lógica o permitida."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'ESTADO_INVALIDO'
    default_detail = 'La transición de estado no está permitida.'


class EncomiendaYaEntregadaError(APIException):
    """Error cuando se intenta modificar una encomienda que ya finalizó su proceso."""
    status_code = status.HTTP_409_CONFLICT
    default_code = 'YA_ENTREGADA'
    default_detail = 'La encomienda ya fue entregada y no puede modificarse.'


# --- 2. Handler Global de Excepciones ---

def encomiendas_exception_handler(exc, context):
    """
    Handler global de errores para la API de encomiendas.
    Garantiza que TODA la API devuelva errores con el mismo formato JSON.
    """
    # Primero procesar con el handler por defecto de DRF para obtener la
    # respuesta inicial
    response = exception_handler(exc, context)

    if response is not None:
        # Determinar el código semántico y el mensaje amigable según el Status
        # Code
        error_code = 'API_ERROR'
        message = 'Ha ocurrido un error procesando la solicitud.'

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_code = 'VALIDATION_ERROR'
            message = 'Los datos enviados contienen errores de validación.'

        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = 'AUTHENTICATION_REQUIRED'
            message = 'Se requiere autenticación para acceder a este recurso.'

        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_code = 'PERMISSION_DENIED'
            message = 'No tienes permiso para realizar esta acción.'

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            error_code = 'NOT_FOUND'
            message = 'El recurso solicitado no existe.'

        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_code = 'RATE_LIMIT_EXCEEDED'
            message = 'Se excedió el límite de solicitudes. Intenta más tarde.'

        elif response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_code = 'BUSINESS_LOGIC_ERROR'
            message = 'La operación no se puede realizar por reglas de negocio.'

        # Reestructurar la respuesta para que siempre tenga el mismo esquema
        response.data = {
            'error': True,
            # Usa el código de la excepción si existe
            'code': getattr(exc, 'default_code', error_code),
            'message': message,
            'detail': response.data,
        }
        return response

    # --- 3. Manejo de Errores no controlados (Errores 500) ---

    # Loguear el error para que los desarrolladores puedan revisarlo en el
    # servidor
    logger.error(
        f'Error no controlado en {context["view"].__class__.__name__}: {exc}',
        exc_info=True
    )

    return Response({
        'error': True,
        'code': 'INTERNAL_ERROR',
        'message': 'Error interno del servidor.',
        'detail': str(exc) if True else None,  # Cambiar a None en producción
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
