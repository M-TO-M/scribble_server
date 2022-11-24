from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.feed.views import *

app_name = 'feed'

router = DefaultRouter(trailing_slash=False)
router.register("", MainFeedViewSet, basename="feed")

urlpatterns = [path('', include(router.urls)), ]
