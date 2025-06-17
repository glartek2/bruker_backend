import json
from django.core.management.base import BaseCommand
from pathlib import Path

from classroom_scheduler.models import Building, Equipment, Room
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Populate the database with test data from JSON files'

    def handle(self, *args, **kwargs):
        base_path = Path(__file__).resolve().parent.parent/ 'test_data'
        print(base_path)
        with open(base_path / 'Users.json') as f:
            users = json.load(f)
            for user_data in users:
                user, created = CustomUser.objects.get_or_create(**user_data)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Skipped'} user: {user.username}"))

        with open(base_path / 'Building.json') as f:
            buildings = json.load(f)
            for building_data in buildings:
                building, created = Building.objects.get_or_create(**building_data)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Skipped'} building: {building.name}"))

        with open(base_path / 'Rooms.json') as f:
            rooms = json.load(f)
            for room_data in rooms:
                building_data = room_data.pop('building')
                building = Building.objects.get(name=building_data)
                equipment_data = room_data.pop('equipment_data')
                equipment, _ = Equipment.objects.get_or_create(**equipment_data)
                room, created = Room.objects.get_or_create(building=building, equipment=equipment, **room_data)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Skipped'} room: {room.room_number}"))
        