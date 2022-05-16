from django.urls import path

from api.contents.views import *


app_name = 'contents'

urlpatterns = [
    path('book/new', BookView.as_view(), name='book_new'),
    path('notes/new', NoteView.as_view(), name='note_new'),
    path('notes/<int:pk>', NoteView.as_view(), name='note_detail'),
    path('notes/<int:pk>/delete', NoteView.as_view(), name='note_delete'),
    path('notes/<int:pk>/like', NoteLikeView.as_view(), name='note_like'),
    path('notes/<int:pk>/like/cancel', NoteLikeCancelView.as_view(), name='note_like_cancel'),
]
