from django.urls import include, path
from rest_framework_simplejwt.views import token_refresh


urlpatterns = [
    path('users/', include('api.users.urls')),
    path('contents/', include('api.contents.urls')),
    path('token/refresh', token_refresh, name='token_refresh'),
]
