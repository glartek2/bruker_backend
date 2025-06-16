from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'home_module'

router = DefaultRouter()
router.register('buildings', views.BuildingViewSet)
router.register('equipment', views.EquipmentViewSet)
router.register('rooms', views.RoomViewSet)
router.register('reservation-info', views.ReservationInfoViewSet)
router.register('reservation', views.ReservationViewSet)
router.register("class_groups", views.ClassGroupViewSet)
urlpatterns = [
    path('', views.home, name='home page'),
    path(
        'api/reservation_update_confirmation/<uidb64>/<token>/<reservation_id>/',
        views.ReservationUpdateConfirmationView.as_view(),
        name='reservation_update_confirmation'
    ),
    path('api/', include(router.urls))
]
