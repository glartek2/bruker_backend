"""
URL configuration for bruker_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from classroom_scheduler import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('classroom_scheduler.urls')),
    path("users/", include("users.urls", namespace='users')),

    # Buildings
    path('buildings/', views.BuildingListView.as_view(), name='building-list'),
    path('buildings/add/', views.BuildingCreateView.as_view(), name='building-add'),
    path('buildings/<int:pk>/', views.BuildingDetailView.as_view(), name='building-detail'),
    path('buildings/<int:pk>/edit/', views.BuildingUpdateView.as_view(), name='building-edit'),
    path('buildings/<int:pk>/delete/', views.BuildingDeleteView.as_view(), name='building-delete'),

    # Rooms
    path('rooms/', views.RoomListView.as_view(), name='room-list'),
    path('rooms/add/', views.RoomCreateView.as_view(), name='room-add'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('rooms/<int:pk>/edit/', views.RoomUpdateView.as_view(), name='room-edit'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room-delete'),

    # Equipment
    path('equipment/', views.EquipmentListView.as_view(), name='equipment-list'),
    path('equipment/add/', views.EquipmentCreateView.as_view(), name='equipment-add'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),
    path('equipment/<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='equipment-edit'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment-delete'),


]
