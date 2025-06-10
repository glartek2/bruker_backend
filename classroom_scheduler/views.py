from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from .models import Building, Room, Equipment, Reservation, ReservationInfo
from .serializers import BuildingSerializer, RoomSerializer, EquipmentSerializer, ReservationInfoSerializer, \
    ReservationSerializer
from .filters import DynamicJsonFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime


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

    @action(detail=False, methods=['get'])
    def available(self, request):
        start_time = request.query_params.get('start')
        end_time = request.query_params.get('end')

        if not start_time or not end_time:
            return Response({'error': 'Enter start and end params (ISO 8601).'}, status=400)

        start_dt = parse_datetime(start_time)
        end_dt = parse_datetime(end_time)

        if not start_dt or not end_dt:
            return Response({'error': 'Incorrect date format. Use ISO 8601.'}, status=400)

        overlapping_reservations = Reservation.objects.filter(
            date_time__gte=start_dt,
            date_time__lt=end_dt
        ).values_list('room_id', flat=True)

        available_rooms = Room.objects.exclude(id__in=overlapping_reservations)

        django_filter = DjangoFilterBackend()
        available_rooms = django_filter.filter_queryset(request, available_rooms, self)

        dynamic_filter = DynamicJsonFilterBackend()
        available_rooms = dynamic_filter.filter_queryset(request, available_rooms, self)

        serializer = self.get_serializer(available_rooms, many=True)
        return Response(serializer.data)


class ReservationInfoViewSet(viewsets.ModelViewSet):
    queryset = ReservationInfo.objects.all()
    serializer_class = ReservationInfoSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
