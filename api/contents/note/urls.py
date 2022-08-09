from django.urls import path

from api.contents.note.views import *

app_name = 'notes'

urlpatterns = [
    path('new', NoteView.as_view(http_method_names=['post']), name='note_new'),
    path('<int:pk>', NoteView.as_view(http_method_names=['get']), name='note_detail'),
    path('<int:pk>/delete', NoteView.as_view(http_method_names=['delete']), name='note_delete'),
    path('<int:pk>/like', NoteLikeView.as_view(http_method_names=['post']), name='note_like'),
    path('<int:pk>/like/cancel', NoteLikeView.as_view(http_method_names=['delete']), name='note_like_cancel'),

]
