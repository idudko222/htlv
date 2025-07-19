from django.contrib import admin
from django.urls import path, include
from results import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'matches', views.MatchStatsViewSet, basename='match')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/teams', views.TeamViewSet.as_view({'get': 'list'}), name='teams'),
    path('api/', include(router.urls)),
]
