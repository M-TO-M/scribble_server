from django.urls import path

from api.contents.book_object.views import *

app_name = 'books'

urlpatterns = [
    path('new', BookView.as_view(), name='book_new'),
    path('search/tagging', TaggingBookSearchAPIView.as_view(), name='tagging_book_search'),
    path('search/navbar', NavbarBookSearchAPIView.as_view(), name='navbar_book_search'),
]
