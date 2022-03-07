# from django.contrib import admin
from django.urls import path
from django.urls.conf import include
from django.conf import settings
from django.conf.urls.static import static
from setting.api import views


urlpatterns = [
    path('auth/', include('authentication.api.urls')),
    path('profile/', include('myprofile.api.urls')),
    path('common/', include('common.api.urls')),
    path('setting/', include('setting.api.urls')),
    path('chat/', include('chat.api.urls')),
    path('about-us/policy', views.PrivacyPolicy.as_view()),
    path('about-us/support', views.DoffySupport.as_view()),
    path('about-us/terms', views.TermsOfUse.as_view()),
    path('about-us/guideline', views.UserGuide.as_view()),
    path('linh-ngao/', views.LinhNgao.as_view())
]

# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
