from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ConversacionAprobarView, ConversacionCerrarView, ConversacionViewSet, LeadChatView,
    LeadViewSet, OportunidadViewSet, TutorPreguntarView, TutorRegistrarInteresView,
)

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'oportunidades', OportunidadViewSet, basename='oportunidad')
router.register(r'conversaciones', ConversacionViewSet, basename='conversacion')

urlpatterns = [
    path('', include(router.urls)),
    path('leads/<int:pk>/chat/', LeadChatView.as_view(), name='lead-chat'),
    path('conversaciones/<int:pk>/cerrar/', ConversacionCerrarView.as_view(), name='conversacion-cerrar'),
    path('conversaciones/<int:pk>/aprobar/', ConversacionAprobarView.as_view(), name='conversacion-aprobar'),
    path('tutor/preguntar/', TutorPreguntarView.as_view(), name='tutor-preguntar'),
    path('tutor/registrar-interes/', TutorRegistrarInteresView.as_view(), name='tutor-registrar-interes'),
]