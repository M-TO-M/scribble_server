from django.urls import include, path
from rest_framework.permissions import AllowAny

from core.views import ScribbleTokenRefreshView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from utils.swagger import ScribbleOpenAPISchemaGenerator

schema_view = get_schema_view(
    openapi.Info(
        title="Scribble Backend API",
        default_version="dev",
        description="Scribble 프로젝트 backend API 문서"
    ),
    public=True,
    permission_classes=(AllowAny,),
    generator_class=ScribbleOpenAPISchemaGenerator,
)

urlpatterns = [
    path('users/', include('api.users.urls')),
    path('contents/', include('api.contents.urls')),
    path('main/', include('api.main.urls')),
    path('token/refresh', ScribbleTokenRefreshView.as_view(), name='token_refresh'),
    path('swagger', schema_view.with_ui('swagger', cache_timeout = 0), name='schema-swagger-ui'),
    path('docs', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

