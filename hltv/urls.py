from django.contrib import admin
from django.urls import path, include
from results import views
from rest_framework import routers

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/matches', views.MatchViewSet.as_view({'get': 'list'}), name='matches'),
]
