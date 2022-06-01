from django.urls import path

from api.contents.book_object.views import *
from api.contents.note.views import *
from api.contents.page.views import *
from api.contents.page_comment.views import *


app_name = 'contents'

urlpatterns = [
    path('naver/search', NaverSearchAPIView.as_view(), name='naver_search'),

    path('book/new', BookView.as_view(), name='book_new'),
    path('notes/new', NoteView.as_view(http_method_names=['post']), name='note_new'),
    path('notes/<int:pk>', NoteView.as_view(http_method_names=['get']), name='note_detail'),
    path('notes/<int:pk>/delete', NoteView.as_view(http_method_names=['delete']), name='note_delete'),
    path('notes/<int:pk>/like', NoteLikeView.as_view(http_method_names=['post']), name='note_like'),
    path('notes/<int:pk>/like/cancel', NoteLikeView.as_view(http_method_names=['delete']), name='note_like_cancel'),

    path('pages/new', PageView.as_view(http_method_names=['post']), name='page_new'),
    path('pages/<int:pk>', PageView.as_view(http_method_names=['get']), name='page_detail'),
    path('pages/<int:pk>/edit', PageView.as_view(http_method_names=['patch']), name='page_edit'),
    path('pages/<int:pk>/delete', PageView.as_view(http_method_names=['delete']), name='page_delete'),
    path('pages/<int:pk>/like', PageLikeView.as_view(http_method_names=['post']), name='page_like'),
    path('pages/<int:pk>/like/cancel', PageLikeView.as_view(http_method_names=['delete']), name='page_like_cancel'),

    path('page_comments/new', PageCommentView.as_view(http_method_names=['post']), name='page_comment_new'),
    path('page_comments/<int:pk>', PageCommentView.as_view(http_method_names=['get']), name='page_comment_detail'),
    path('page_comments/<int:pk>/edit', PageCommentView.as_view(http_method_names=['patch']), name='page_comment_edit'),
    path('page_comments/<int:pk>/delete', PageCommentView.as_view(http_method_names=['delete']), name='page_comment_delete'),
]
