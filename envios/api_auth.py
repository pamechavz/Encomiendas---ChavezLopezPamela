from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login


class EncomiendaTokenView(TokenObtainPairView):
    """Clase para obtener el token JWT"""
    pass


class LoginCookieView(APIView):
    """Clase para login por cookies"""

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return Response({"message": "Sesión iniciada"})
        return Response({"error": "Credenciales inválidas"}, status=401)
