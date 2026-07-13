from rest_framework import serializers

from .models import Conversacion, Lead, Mensaje, Oportunidad, TutorSesion


class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ['id', 'emisor', 'contenido', 'timestamp']


class ConversacionSerializer(serializers.ModelSerializer):
    mensajes = MensajeSerializer(many=True, read_only=True)

    class Meta:
        model = Conversacion
        fields = [
            'id', 'lead', 'canal', 'iniciada_en', 'finalizada_en', 'resumen',
            'objeciones', 'siguiente_accion_sugerida', 'estado_aprobacion',
            'aprobada_por', 'mensajes',
        ]
        read_only_fields = ['id', 'iniciada_en', 'aprobada_por']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'cliente', 'tipo', 'nombre_contacto', 'email', 'telefono',
            'interes', 'presupuesto_estimado', 'urgencia', 'prioridad_score',
            'etapa_embudo', 'origen', 'is_active', 'created_at', 'modified_at',
        ]
        read_only_fields = ['id', 'prioridad_score', 'created_at', 'modified_at']


class OportunidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oportunidad
        fields = ['id', 'lead', 'linea_servicio', 'descripcion', 'valor_estimado', 'estado', 'created_at']
        read_only_fields = ['id', 'created_at']


class TutorSesionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TutorSesion
        fields = [
            'id', 'lead', 'tema_interes', 'fuente_contenido',
            'quiz_score', 'consentimiento_registrado', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']