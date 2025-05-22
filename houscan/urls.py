from django.contrib import admin
from django.urls import path, include
from .views import root 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', root),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/profile/', include('profiles.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/announcements/', include('announcements.urls')),
]
  
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)