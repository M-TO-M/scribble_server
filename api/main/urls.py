from django.urls import path

from api.main.views import *

app_name = 'main'

urlpatterns = [
    path('', MainView.as_view(), name='main'),
    path('<int:pk>', UserMainView.as_view(), name='user_main'),
    path('<int:pk>/books', BookListView.as_view(), name='main_book_list'),
]
