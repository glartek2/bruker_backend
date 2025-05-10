from rest_framework import serializers
from .models import Building, Equipment, Room


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
