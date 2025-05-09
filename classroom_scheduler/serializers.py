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
    building = EquipmentSerializer(read_only=True)

    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(),
        source='building',
        write_only=True
    )

    class Meta:
        model = Room
        fields = ['id', 'capacity', 'room_number', 'building', 'equipment', 'building_id', 'equipment_id']
