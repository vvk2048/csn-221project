
"""newscatcher_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse

from api import views, googleviews, socialviews, dbviews

from rest_framework_simplejwt import views as jwt_views
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

router = DefaultRouter()
router.register(r'mytag', views.MyTagViewSet)
router.register(r'mycategory', views.MyCategoryViewSet)
router.register(r'mynews', views.MyNewsViewSet)
router.register(r'save', views.SaveViewSet)
router.register(r'vote', views.VoteViewSet)

router.register(r'organization', views.OrganizationViewSet)
router.register(r'profile', views.ProfileViewSet)
router.register(r'profile-info', views.ProfileInfoViewSet)
router.register(r'competition', views.CompViewSet)


urlpatterns = [
    path('stats/', googleviews.Stats.as_view(), name='app_stats'),
    path('un/', dbviews.UpdateNews.as_view(), name='update_news'),
    path('auth/google/', googleviews.GoogleLogin.as_view(), name='goggle_login'),
    path('auth/facebook/', socialviews.FacebookLogin.as_view(), name='fb_connect'),
    path('auth/twitter/', socialviews.TwitterLogin.as_view(), name='twitter_connect'),
    path('auth/github/', socialviews.GithubLogin.as_view(), name='github_connect'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('category/', views.CategoryView.as_view()),
    path('tag/', views.TagView.as_view()),
    path('topic/', views.TopicView.as_view()),
    path('quote/', views.QuoteView.as_view()),
    path('news/', views.NewsView.as_view()),
    path('event/', views.EventView.as_view()),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('', include(router.urls)),
    path('openapi/', get_schema_view(
        title="BlueBird",
        description="API for all things …",
        version="1.0.0"
    ), name='openapi-schema'),
    path('swagger-ui/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='swagger-ui'),
    path('current_version/', lambda x: JsonResponse({'version': 1}))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
