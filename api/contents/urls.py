from django.urls import include, path

app_name = 'contents'

urlpatterns = [
    path('books/', include('api.contents.book_object.urls')),
    path('notes/', include('api.contents.note.urls')),
    path('pages/', include('api.contents.page.urls')),
    path('page_comments/', include('api.contents.page_comment.urls')),
]
