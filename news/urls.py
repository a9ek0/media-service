from django.urls import path
from django.views.generic import TemplateView

from . import views
from .views import image_list, upload_image

app_name = 'news'

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html")),
    path('upload/', views.upload_image, name='upload_image'),
    path('images/', image_list, name='image_list'),
    path('editorjs/upload_file/', upload_image, name='editorjs-upload-file'),
]
