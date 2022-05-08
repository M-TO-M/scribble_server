from django.urls import path

from api.contents.views import *


app_name = 'contents'

urlpatterns = [
    path('book/new', BookView.as_view(), name='book_new'),
]
