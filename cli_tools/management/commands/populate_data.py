import json
from django.core.management.base import BaseCommand
from pathlib import Path
from django.urls import reverse
from rest_framework.test import APIClient

from classroom_scheduler.models import Building, ClassGroup, Equipment, ReservationInfo, Room
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Populate the database with test data from JSON files'

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username="admin").exists():
            CustomUser.objects.create_superuser(username="admin", email="admin@mail.mail", password="admin123")
        base_path = Path(__file__).resolve().parent.parent/ 'test_data'
        with open(base_path / 'Users.json') as f:
            users = json.load(f)
            for user_data in users:
                if CustomUser.objects.filter(**user_data).exists():
                    continue
                user= CustomUser.objects.create_user(**user_data)
                self.stdout.write(self.style.SUCCESS(f"{'Created'} user: {user.username}"))

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

        with open(base_path / 'Groups.json') as f:
            groups = json.load(f)
            for group_data in groups:
                members = [CustomUser.objects.get(username=name).pk for name in group_data.pop('members')]
                class_rep = [CustomUser.objects.get(username=name).pk for name in group_data.pop('class_representatives')]
                instructors = [CustomUser.objects.get(username=name).pk for name in group_data.pop('instructors')]

                group, created = ClassGroup.objects.get_or_create(**group_data)
                if created:
                    for mem in members:
                        group.members.add(mem)
                    for rep in class_rep:
                        group.class_representatives.add(rep)
                    for inst in instructors:
                        group.instructors.add(inst)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Skipped'} class group: {group.name}"))

        with open(base_path / 'Reservations.json') as f:
            admin= CustomUser.objects.get(username='admin')
            client = APIClient()
            client.force_authenticate(user=admin)
            reservations = json.load(f)
            for res_data in reservations:
                res_info_data = res_data.pop('reservation_info')

                # create reservation info
                user = CustomUser.objects.get(username=res_info_data.pop('user'))
                group = ClassGroup.objects.get(name=res_info_data.pop('group'))
                res_info, created1 = ReservationInfo.objects.get_or_create(user=user, group=group, **res_info_data)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created1 else 'Skipped'} reservation info: {res_info.description}"))

                room = Room.objects.get(room_number = res_data.pop('room'))

                payload = {
                    "room_id": room.pk,
                    "reservation_info_id": res_info.pk,
                    "date_times": res_data.pop('date_time')
                }

                resp= client.post(reverse("home_module:reservation-bulk-create-reservation"), data=payload, format='json')

                if resp.status_code == 201:
                    self.stdout.write(self.style.SUCCESS("Batch created successfully."))
                else:
                    self.stderr.write(self.style.ERROR(f"Error: {resp.status_code} - {resp.json()}"))