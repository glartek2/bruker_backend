from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from .models import Building, Room, Equipment, Reservation, ReservationInfo
from .serializers import BuildingSerializer, RoomSerializer, EquipmentSerializer, ReservationInfoSerializer, \
    ReservationSerializer
from .filters import DynamicJsonFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter


def home(request):
    return HttpResponse('Classroom scheduler home page')


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['name', 'address', 'department']
    search_fields = ['name', 'address', 'department', 'description']


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filter_backends = [SearchFilter]
    search_fields = ['details']


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('building', 'equipment').all()
    serializer_class = RoomSerializer
    filter_backends = [DjangoFilterBackend, DynamicJsonFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'capacity': ['exact', 'gte', 'lte'],
        'room_number': ['exact', 'icontains'],
        'building__name': ['exact', 'icontains'],
    }

    search_fields = ['room_number', 'building__name']
    ordering_fields = ['capacity', 'room_number', 'building__name']


class ReservationInfoViewSet(viewsets.ModelViewSet):
    queryset = ReservationInfo.objects.all()
    serializer_class = ReservationInfoSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
