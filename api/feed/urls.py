from django.urls import path

from api.feed.views import *

app_name = 'feed'

urlpatterns = [
    path('', MainView.as_view(), name='main'),
    path('<int:pk>', UserMainView.as_view(), name='user_main'),
    path('<int:pk>/notes', NoteListView.as_view(), name='main_note_list'),
]
