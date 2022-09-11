from django.urls import path

from api.contents.page.views import *

app_name = 'pages'

urlpatterns = [
    path('new', PageView.as_view(http_method_names=['post']), name='page_new'),
    path('<int:pk>', PageView.as_view(http_method_names=['get']), name='page_detail'),
    path('<int:pk>/edit', PageView.as_view(http_method_names=['patch']), name='page_edit'),
    path('<int:pk>/delete', PageView.as_view(http_method_names=['delete']), name='page_delete'),
    path('<int:pk>/like', PageLikeView.as_view(http_method_names=['post']), name='page_like'),
    path('<int:pk>/like/cancel', PageLikeView.as_view(http_method_names=['delete']), name='page_like_cancel'),
    path('all/<int:isbn>', PageAllView.as_view(http_method_names=['get']), name='page_all'),
]
