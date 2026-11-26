import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from peso.views import CustomLoginView, UserRegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('', include(('peso.urls', 'database'), namespace='database')),
]

if settings.DEBUG:
    if settings.STATICFILES_DIRS and os.path.exists(settings.STATICFILES_DIRS[0]):
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    if hasattr(settings, 'MEDIA_ROOT') and os.path.exists(settings.MEDIA_ROOT):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
