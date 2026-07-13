from django.contrib import admin

from .models import Conversacion, Lead, Mensaje, Oportunidad, TutorSesion


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_contacto', 'tipo', 'etapa_embudo', 'prioridad_score', 'urgencia')
    list_filter = ('tipo', 'etapa_embudo', 'urgencia')


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'estado_aprobacion', 'siguiente_accion_sugerida', 'iniciada_en')
    list_filter = ('estado_aprobacion', 'siguiente_accion_sugerida')


admin.site.register(Oportunidad)
admin.site.register(Mensaje)
admin.site.register(TutorSesion)