from django.urls import include, path


urlpatterns = [
    path('users/', include('api.users.urls')),
    path('contents/', include('api.contents.urls')),
]
