from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from rest_framework.authtoken.views import obtain_auth_token

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from news.views import upload_image

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('news.urls')),
    path('api/', include('news.api_urls')),
    path('editorjs/upload_file/', upload_image, name='editorjs-upload-file'),
    path('api-token-auth/', obtain_auth_token),
    path('editorjs/', include('django_editorjs2.urls')),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)