from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'home_module'

router = DefaultRouter()
router.register('buildings', views.BuildingViewSet)
router.register('equipment', views.EquipmentViewSet)
router.register('rooms', views.RoomViewSet)
urlpatterns = [
    path('', views.home, name='home page'),
    path('api/', include(router.urls))
]
