from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

from news.views import upload_image

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('news.urls')),
    path('api/', include('news.api_urls')),
    path('editorjs/upload_file/', upload_image, name='editorjs-upload-file'),
    path('api-token-auth/', obtain_auth_token),
    path('editorjs/', include('django_editorjs2.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)