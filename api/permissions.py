from rest_framework import permissions

class EsEmpleadoActivo(permissions.BasePermission):
    """Solo permite acceso si el usuario está activo"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)

class EsPropietarioOAdmin(permissions.BasePermission):
    """Permite si es staff o si es el dueño del registro"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.empleado_registro.user == request.user