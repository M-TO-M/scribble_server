from django.urls import path

from api.users.views import *


app_name = 'users'

urlpatterns = [
    path('new', SignUpView.as_view(), name='signup'),
    path('verify', VerifyView.as_view(), name='verify'),
    path('signin', SignInView.as_view(), name='signin'),
    path('signout', SignOutView.as_view(), name='signout'),
    path('<int:pk>/delete', UserView.as_view(http_method_names=['delete']), name='user_delete'),
    path('<int:pk>/edit', UserView.as_view(http_method_names=['patch']), name='user_edit'),
    path('<int:pk>/category', CategoryView.as_view(http_method_names=['get']), name='user_category'),
    path('category', CategoryView.as_view(http_method_names=['patch']), name='category_follow_unfollow'),
    path('<int:pk>/passwd/change', PasswordView.as_view(), name='passwd_change'),
    path('myinfo', UserInfoByTokenView.as_view(), name='user_info'),
]
