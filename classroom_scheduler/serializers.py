from rest_framework import serializers
from .models import Building, Equipment, Room, Reservation, ReservationInfo
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


class ReservationInfoSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='user',
        write_only=True
    )
    class_representatives = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )

    class Meta:
        model = ReservationInfo
        fields = ['id', 'user', 'user_id', 'class_representatives', 'description']


class ReservationSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    reservation_info = ReservationInfoSerializer(read_only=True)

    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        source='room',
        write_only=True
    )
    reservation_info_id = serializers.PrimaryKeyRelatedField(
        queryset=ReservationInfo.objects.all(),
        source='reservation_info',
        write_only=True
    )

    reservation_info_data = ReservationInfoSerializer(
        source='reservation_info',
        write_only=True,
        required=False
    )

    class Meta:
        model = Reservation
        fields = [
            'id', 'room', 'room_id', 'reservation_info',
            'reservation_info_id', 'reservation_info_data', 'date_time',
            'proposed_date_time'
        ]

    def create(self, validated_data):
        reservation_info = validated_data.pop('reservation_info', None)
        room_obj = validated_data.pop('room')

        if isinstance(reservation_info, dict):
            user_data = reservation_info.pop('user')
            user_obj = CustomUser.objects.get(id=user_data['id'])
            reservation_info, _ = ReservationInfo.objects.get_or_create(
                user=user_obj,
                defaults=reservation_info
            )

        reservation = Reservation.objects.create(
            room=room_obj,
            reservation_info=reservation_info,
            **validated_data
        )

        return reservation
