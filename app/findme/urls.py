# from django.contrib import admin
from django.urls import path
from django.urls.conf import include
# from django.conf import settings
# from django.conf.urls.static import static
from setting.api import views


urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('profile/', include('myprofile.urls')),
    path('common/', include('common.urls')),
    path('setting/', include('setting.api.urls')),
    path('chat/', include('chat.urls')),
    path('about-us/policy', views.PrivacyPolicy.as_view()),
    path('about-us/support', views.DoffySupport.as_view()),
    path('about-us/terms', views.TermsOfUse.as_view()),
    # path('about-us/guideline', views.UserGuide.as_view()),
    path('', views.LandingPage.as_view()),
]

# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
