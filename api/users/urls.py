from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.users.views import *


app_name = 'users'
router = DefaultRouter(trailing_slash=False)
router.register("", UserViewSet, basename="")
router.register("passwd", PasswordViewSet, basename="passwd")

urlpatterns = [path('', include(router.urls)), ]
