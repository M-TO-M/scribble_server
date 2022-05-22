from django.urls import include, path
from core.views import ScribbleTokenRefreshView


urlpatterns = [
    path('users/', include('api.users.urls')),
    path('contents/', include('api.contents.urls')),
    path('token/refresh', ScribbleTokenRefreshView.as_view(), name='token_refresh'),
]
