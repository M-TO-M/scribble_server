from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.contents.views import *

app_name = 'contents'
router = DefaultRouter(trailing_slash=False)
router.register("books", BookViewSet, basename="books")
router.register("notes", NoteViewSet, basename="notes")
router.register("pages", PageViewSet, basename="pages")
router.register("page_comments", PageCommentViewSet, basename="page_comments")

urlpatterns = [path('', include(router.urls)), ]
