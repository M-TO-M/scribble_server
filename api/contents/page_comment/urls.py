from django.urls import path

from api.contents.page_comment.views import *

app_name = 'page_comments'

urlpatterns = [
    path('new', PageCommentView.as_view(http_method_names=['post']), name='page_comment_new'),
    path('<int:pk>', PageCommentView.as_view(http_method_names=['get']), name='page_comment_detail'),
    path('<int:pk>/edit', PageCommentView.as_view(http_method_names=['patch']), name='page_comment_edit'),
    path('<int:pk>/delete', PageCommentView.as_view(http_method_names=['delete']), name='page_comment_delete'),
]
