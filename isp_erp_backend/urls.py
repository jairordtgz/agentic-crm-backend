from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from cliente.views import ClienteViewSet
from linea.views import LineaServicioViewSet
from core.views import healthcheck, metricas_basicas
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'lineas', LineaServicioViewSet, basename='linea')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/token/', obtain_auth_token, name='api-token-auth'),
    path('api/health/', healthcheck, name='healthcheck'),
    path('api/metrics/', metricas_basicas, name='metricas'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/crm/', include('crm_agent.urls')),
]