from typing import Counter
from rest_framework import serializers
from .models import Building, Equipment, Room, Reservation, ReservationInfo, ClassGroup
from users.serializers import CustomUserSerializer
from users.models import CustomUser


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'name', 'address', 'department', 'description']


class EquipmentSerializer(serializers.ModelSerializer):
    details = serializers.DictField(child=serializers.JSONField())

    class Meta:
        model = Equipment
        fields = ['id', 'details']


class RoomSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    building = BuildingSerializer(read_only=True)

    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True,
        required=False,
    )
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        source='building',
        write_only=True,
        required=False,
    )

    equipment_data = EquipmentSerializer(
        source='equipment',
        write_only=True,
        required=False,
    )

    building_data = BuildingSerializer(
        source='building',
        write_only=True,
        required=False,
    )

    class Meta:
        model = Room
        fields = [
            'id',
            'capacity',
            'room_number',
            'building',
            'equipment',
            'building_data',
            'equipment_data',
            'building_id',
            'equipment_id'
        ]

    def create(self, validated_data):

        building_obj = validated_data.pop('building')

        if isinstance(building_obj, dict):
            b_data = building_obj
            building_obj = Building.objects.get_or_create(
                name=b_data['name'],
                address=b_data['address'],
                defaults={
                    'department': b_data.get('department', ''),
                    'description': b_data.get('description', '')
                }

            )[0]

        equipment_obj = validated_data.pop('equipment')

        if isinstance(equipment_obj, dict):
            e_data = equipment_obj
            equipment_obj = Equipment.objects.get_or_create(
                details=e_data['details']
            )[0]

        room = Room.objects.create(
            building=building_obj,
            equipment=equipment_obj,
            **validated_data
        )

        return room


class ClassGroupSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )
    class_representatives = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )
    instructors = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = ClassGroup
        fields = ['id', 'name', 'members', 'class_representatives', 'instructors']


class ReservationInfoSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='user',
        write_only=True
    )
    group = ClassGroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=ClassGroup.objects.all(),
        source='group',
        write_only=True
    )

    class Meta:
        model = ReservationInfo
        fields = ['id', 'user', 'user_id', 'group', 'group_id', 'description']


class ReservationSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    reservation_info = ReservationInfoSerializer(read_only=True)
    proposed_room = RoomSerializer(read_only=True)

    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        source='room',
        write_only=True
    )
    proposed_room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        source='proposed_room',
        write_only=True,
        required=False
    )
    reservation_info_id = serializers.PrimaryKeyRelatedField(
        queryset=ReservationInfo.objects.all(),
        source='reservation_info',
        write_only=True,
        required=False
    )
    reservation_info_data = ReservationInfoSerializer(
        source='reservation_info',
        write_only=True,
        required=False
    )

    class Meta:
        model = Reservation
        fields = [
            'id', 'room', 'room_id',
            'proposed_room', 'proposed_room_id',
            'reservation_info', 'reservation_info_id', 'reservation_info_data',
            'date_time', 'proposed_date_time'
        ]

    def validate(self, attrs):
        if 'reservation_info' not in attrs or attrs['reservation_info'] is None:
            raise serializers.ValidationError(
                "Either reservation_info_id or reservation_info_data must be provided"
            )
        return attrs

    def create(self, validated_data):
        reservation_info_data = validated_data.pop('reservation_info', None)
        room = validated_data.pop('room')
        proposed_room = validated_data.pop('proposed_room', None)

        if isinstance(reservation_info_data, dict):
            lookup = {
                'user': reservation_info_data.pop('user'),
                'group': reservation_info_data.pop('group', None)
            }
            if 'description' in reservation_info_data:
                lookup['description'] = reservation_info_data.pop('description')
            
            reservation_info, _ = ReservationInfo.objects.get_or_create(
                **lookup,
                defaults=reservation_info_data
            )
        else:
            reservation_info = reservation_info_data

        reservation = Reservation.objects.create(
            room=room,
            proposed_room=proposed_room,
            reservation_info=reservation_info,
            **validated_data
        )

        return reservation

class BulkReservationSerializer(serializers.Serializer):
    room_id = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    reservation_info_id = serializers.PrimaryKeyRelatedField(
        queryset=ReservationInfo.objects.all(),
        source='reservation_info',
        write_only=True,
        required=False
    )
    reservation_info_data = ReservationInfoSerializer(
        source='reservation_info',
        write_only=True,
        required=False
    )
    date_times = serializers.ListField(
        child=serializers.DateTimeField(),
        allow_empty=False
    )

    def validate(self, attrs):
        if 'reservation_info' not in attrs or attrs['reservation_info'] is None:
            raise serializers.ValidationError(
                "Either reservation_info_id or reservation_info_data must be provided"
            )
        room = attrs['room_id']
        date_times = attrs['date_times']
        dt_counts = Counter(date_times)
        duplicated = [dt for dt, count in dt_counts.items() if count > 1]
        if duplicated:
            raise serializers.ValidationError(
                {"date_times": f"Duplicate date_times in input: {duplicated}"}
            )

        for dt in date_times:
            if Reservation.objects.filter(room=room, date_time=dt).exists():
                raise serializers.ValidationError(
                    f"Room '{room}' is already booked for {dt}"
                )

        return attrs
    
    def create(self, validated_data):
        room = validated_data['room_id']
        date_times = validated_data['date_times']
        reservation_info_data = validated_data.pop('reservation_info', None)

        if isinstance(reservation_info_data, dict):
            lookup = {
                'user': reservation_info_data.pop('user'),
                'group': reservation_info_data.pop('group', None)
            }
            if 'description' in reservation_info_data:
                lookup['description'] = reservation_info_data.pop('description')
            reservation_info, _ = ReservationInfo.objects.get_or_create(
                **lookup,
                defaults=reservation_info_data
            )
        else:
            reservation_info = reservation_info_data

        reservations = [
            Reservation(room=room, reservation_info=reservation_info, date_time=dt)
            for dt in date_times
        ]

        return Reservation.objects.bulk_create(reservations)
