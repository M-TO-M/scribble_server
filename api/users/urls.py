from django.urls import path

from api.users.views import *


app_name = 'users'

urlpatterns = [
    path('new', SignUpView.as_view(), name='signup'),
    path('verify', VerifyView.as_view(), name='verify'),
    path('signin', SignInView.as_view(), name='signin'),
]
