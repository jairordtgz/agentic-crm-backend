from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import EsEjecutivoStaff, SoloAdminPuedeEliminar

from .models import Conversacion, Lead, Mensaje, Oportunidad
from .serializers import ConversacionSerializer, LeadSerializer, OportunidadSerializer, TutorSesionSerializer
from .services import gemini_client


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related('cliente').all()
    serializer_class = LeadSerializer
    filterset_fields = ['tipo', 'etapa_embudo', 'is_active']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action == 'destroy':
            return [SoloAdminPuedeEliminar()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class ConversacionViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura, para que el panel de aprobación liste/detalle sin adivinar IDs."""
    queryset = Conversacion.objects.select_related('lead').prefetch_related('mensajes').all()
    serializer_class = ConversacionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['estado_aprobacion', 'lead']


class OportunidadViewSet(viewsets.ModelViewSet):
    queryset = Oportunidad.objects.select_related('lead', 'linea_servicio').all()
    serializer_class = OportunidadSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['lead', 'estado']


class LeadChatView(APIView):
    """Historia 1 — pública, la usa el prospecto sin login."""
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            lead = Lead.objects.get(pk=pk, is_active=True)
        except Lead.DoesNotExist:
            raise ValidationError({'detail': 'Lead no encontrado.'})

        mensaje_usuario = request.data.get('mensaje', '').strip()
        if not mensaje_usuario:
            raise ValidationError({'mensaje': 'El mensaje no puede estar vacío.'})

        conversacion, _ = Conversacion.objects.get_or_create(
            lead=lead, finalizada_en__isnull=True, defaults={'lead': lead},
        )
        Mensaje.objects.create(
            conversacion=conversacion, emisor=Mensaje.Emisor.LEAD, contenido=mensaje_usuario,
        )

        historial = list(conversacion.mensajes.values('emisor', 'contenido'))
        texto_respuesta = gemini_client.responder_chat(historial, lead.tipo)

        Mensaje.objects.create(
            conversacion=conversacion, emisor=Mensaje.Emisor.AGENTE_IA, contenido=texto_respuesta,
        )
        return Response(
            {'conversacion_id': conversacion.id, 'respuesta': texto_respuesta},
            status=status.HTTP_200_OK,
        )


class ConversacionCerrarView(APIView):
    """Historia 3 parte 1 — pública, la dispara el prospecto al terminar de chatear."""
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            conversacion = Conversacion.objects.select_related('lead').get(pk=pk)
        except Conversacion.DoesNotExist:
            raise ValidationError({'detail': 'Conversación no encontrada.'})

        historial = list(conversacion.mensajes.values('emisor', 'contenido'))
        resultado = gemini_client.calificar_lead(historial, conversacion.lead.tipo)

        conversacion.resumen = resultado['resumen_necesidad']
        conversacion.objeciones = resultado['objeciones']
        conversacion.siguiente_accion_sugerida = resultado['siguiente_accion_sugerida']
        conversacion.finalizada_en = timezone.now()
        conversacion.save()

        conversacion.lead.prioridad_score = resultado['prioridad_score']
        conversacion.lead.urgencia = resultado['urgencia']
        conversacion.lead.etapa_embudo = Lead.EtapaEmbudo.CALIFICADO
        conversacion.lead.save()

        return Response(ConversacionSerializer(conversacion).data)


class ConversacionAprobarView(APIView):
    """Historia 3 parte 2 — solo ejecutivos (is_staff)."""
    permission_classes = [EsEjecutivoStaff]

    def post(self, request, pk):
        conversacion = Conversacion.objects.get(pk=pk)
        decision = request.data.get('decision')
        if decision not in dict(Conversacion.EstadoAprobacion.choices):
            raise ValidationError({'decision': 'Valor inválido.'})

        if decision == Conversacion.EstadoAprobacion.EDITADA:
            nueva_accion = request.data.get('nueva_accion')
            if not nueva_accion:
                raise ValidationError({'nueva_accion': 'Requerido cuando decision=EDITADA.'})
            conversacion.siguiente_accion_sugerida = nueva_accion

        conversacion.estado_aprobacion = decision
        conversacion.aprobada_por = request.user
        conversacion.save()

        return Response(ConversacionSerializer(conversacion).data)


class TutorPreguntarView(APIView):
    """Historia 2 — pública."""
    permission_classes = [AllowAny]

    def post(self, request):
        pregunta = request.data.get('pregunta', '').strip()
        if not pregunta:
            raise ValidationError({'pregunta': 'La pregunta no puede estar vacía.'})
        resultado = gemini_client.tutor_responder(pregunta)
        return Response(resultado)


class TutorRegistrarInteresView(APIView):
    """Historia 2 — pública, exige consentimiento explícito."""
    permission_classes = [AllowAny]

    def post(self, request):
        consentimiento = request.data.get('consentimiento_registrado', False)
        if not consentimiento:
            raise ValidationError(
                {'consentimiento_registrado': 'Se requiere consentimiento explícito para registrar esta señal.'}
            )
        serializer = TutorSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)