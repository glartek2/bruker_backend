from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Building, Room, Equipment, Reservation, ReservationInfo, ClassGroup
from .serializers import BuildingSerializer, BulkReservationSerializer, RoomSerializer, EquipmentSerializer, ReservationInfoSerializer, \
    ReservationSerializer, ClassGroupSerializer
from .filters import DynamicJsonFilterBackend
from rest_framework import viewsets, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.utils.dateparse import parse_datetime
from users.views import send_email


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='start',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Start datetime in ISO 8601 format.'
            ),
            OpenApiParameter(
                name='end',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='End datetime in ISO 8601 format.'
            ),
        ],
        responses={200: RoomSerializer(many=True)},
        description='Get rooms available between the given start and end time.'
    )
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
    permission_classes = [IsAuthenticated]
    serializer_class = ReservationInfoSerializer
    queryset = ReservationInfo.objects.none()

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return ReservationInfo.objects.all()

        return ReservationInfo.objects.filter(
            Q(user=user) |
            Q(group__class_representatives=user) |
            Q(group__instructors=user)
        ).distinct()


class ClassGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ClassGroupSerializer
    queryset = ClassGroup.objects.all()


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservationSerializer
    queryset = Reservation.objects.none()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'date_time': ['gte', 'lte']
    }
    
    def get_queryset(self):
        user = self.request.user

        me_param = self.request.query_params.get('me', '').lower()
        force_user_filter = me_param in ['true', '1', 'yes', 'on']

        if (user.is_staff or user.is_superuser) and not force_user_filter:
            return Reservation.objects.all()

        return Reservation.objects.filter(
            Q(reservation_info__user=user) |
            Q(reservation_info__group__class_representatives=user) |
            Q(reservation_info__group__instructors=user)
        ).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = serializer.validated_data.get('room')
        date_time = serializer.validated_data.get('date_time')

        if Reservation.objects.filter(room=room, date_time=date_time).exists():
            return Response(
                {"detail": "A reservation already exists for this room at the given time."},
                status=status.HTTP_409_CONFLICT
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=ReservationSerializer,
        responses={
            200: OpenApiResponse(description="Reservation updated successfully."),
            202: OpenApiResponse(description="Confirmation email sent to reservation owner."),
            403: OpenApiResponse(description="You do not have permission to modify this reservation."),
            400: OpenApiResponse(description="Validation failed.")
        },
        description="Update reservation. Staff can update immediately.Class representatives trigger email confirmation."
    )
    def update(self, request, *args, **kwargs):
        reservation = self.get_object()
        serializer = self.get_serializer(reservation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = request.user

        group = reservation.reservation_info.group
        proposed_date_time = serializer.validated_data.get('proposed_date_time')
        proposed_room = serializer.validated_data.get('proposed_room')

        if group and group.class_representatives.filter(id=user.id).exists():

            reservation.proposed_date_time = proposed_date_time
            reservation.proposed_room = proposed_room
            reservation.save()

            instructor = group.instructors.first()
            if not instructor:
                return Response({"detail": "No instructor assigned to the group."}, status=400)

            extra_context = {
                'requesting_user': user,
                'reservation': reservation,

            }

            send_email(
                request=request,
                user=instructor,
                mail_subject="Reservation date update confirmation",
                token_generator=default_token_generator,
                template_name='reservation_update_confirmation.html',
                to_email=instructor.email,
                extra_context=extra_context
            )

            return Response({
                "detail": "Confirmation email sent to reservation instructor.",
                "reservation_id": reservation.id
            }, status=status.HTTP_202_ACCEPTED)

        elif group and group.instructors.filter(id=user.id).exists():
            reservation.date_time = proposed_date_time
            reservation.room = proposed_room
            reservation.proposed_room = None
            reservation.proposed_date_time = None
            reservation.save()
            return Response({"detail": "Reservation updated successfully."}, status=status.HTTP_200_OK)

        return Response({"detail": "You do not have permission to modify this reservation."},
                        status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create_reservation(self, request):
        serializer = BulkReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Reservations created successfully."}, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        responses={
            204: OpenApiResponse(description="Reservation deleted successfully."),
            403: OpenApiResponse(description="You do not have permission to delete this reservation."),
        },
        description="Delete reservation. Only staff, superusers, and instructors of the group can delete."
    )
    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        user = request.user

        group = reservation.reservation_info.group

        if user == reservation.reservation_info.user:
            reservation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if group and (group.class_representatives.filter(id=user.id).exists() or group.instructors.filter(id=user.id).exists()):
            reservation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "You do not have permission to delete this reservation."},
            status=status.HTTP_403_FORBIDDEN
        )


class ReservationUpdateConfirmationView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter('uidb64', str, OpenApiParameter.PATH),
            OpenApiParameter('token', str, OpenApiParameter.PATH),
            OpenApiParameter('reservation_id', str, OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(description="Reservation updated correctly"),
            400: OpenApiResponse(description="Invalid token or validation error")
        }
    )
    def get(self, request, uidb64, token, reservation_id):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
        except Exception:
            return Response({'detail': "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": 'Token invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        if not reservation_id:
            return Response({"detail": "Reservation ID not provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return Response({"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)

        if not reservation.proposed_date_time:
            return Response({"detail": "No pending update to confirm."}, status=status.HTTP_400_BAD_REQUEST)

        reservation.date_time = reservation.proposed_date_time
        reservation.proposed_date_time = None
        reservation.room = reservation.proposed_room
        reservation.proposed_room = None
        reservation.save()

        return Response({"detail": "Reservation updated correctly."}, status=status.HTTP_200_OK)
