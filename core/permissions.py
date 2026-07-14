from rest_framework.permissions import BasePermission


class SoloAdminPuedeEliminar(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method == 'DELETE':
            return request.user.is_staff
        return True
    
class EsEjecutivoStaff(BasePermission):
    """Exige usuario autenticado y is_staff, sin importar el método HTTP."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)