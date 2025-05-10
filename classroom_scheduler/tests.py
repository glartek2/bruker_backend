from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Building, Equipment, Room
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoomAPITestCase(APITestCase):
    def setUp(self):

        self.b1 = Building.objects.create(
            name="Test Hala", address="ul. Testowa 1",
            department="D", description="Desc"
        )
        self.e1 = Equipment.objects.create(details={"switches": 5, "computers": 12, 'programs': ['linux', 'windows']})
        self.room = Room.objects.create(
            building=self.b1, equipment=self.e1,
            room_number="R1", capacity=20
        )

        self.list_url = reverse('home_module:room-list')
        self.detail_url = lambda pk: reverse('home_module:room-detail', args=[pk])

    def test_list_rooms(self):
        resp = self.client.get(self.list_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_filter_rooms_by_capacity(self):

        params = {'capacity__gte': 10}
        resp = self.client.get(self.list_url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        capacities = [r['capacity'] for r in resp.data]
        self.assertIn(20, capacities)

    def test_filter_rooms_by_building_and_capacity(self):
        params = {'building__name__icontains': 'Test Hala', 'capacity__gte': 10}
        resp = self.client.get(self.list_url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        buildings = [r['building']['name'] for r in resp.data]
        capacities = [r['capacity'] for r in resp.data]

        for building, capacity in zip(buildings, capacities):
            self.assertTrue('Test Hala' in building)
            self.assertGreaterEqual(capacity, 10)

    def test_filter_rooms_by_building_name(self):
        params = {'building__name__icontains': 'Test Hala'}
        resp = self.client.get(self.list_url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        buildings = [r['building']['name'] for r in resp.data]

        for building in buildings:
            self.assertTrue('Test Hala' in building)

    def test_dynamic_json_filter(self):
        resp = self.client.get(self.list_url,
                               {'computers__gte': 10, 'switches__gte': 5, 'programs__contains': 'windows'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        details = [r['equipment']['details'] for r in resp.data]
        logger.info(details)
        self.assertDictEqual(details[0], {"switches": 5, "computers": 12, 'programs': ['linux', 'windows']})

    def test_filter_rooms_by_capacity_range(self):
        params = {'capacity__gte': 10, 'capacity__lte': 30}
        resp = self.client.get(self.list_url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        capacities = [r['capacity'] for r in resp.data]

        for capacity in capacities:
            self.assertGreaterEqual(capacity, 10)
            self.assertLessEqual(capacity, 30)

    def test_filter_rooms_by_programs_icontains_multiple_values(self):
        params = {'programs__contains': 'windows, linux'}
        resp = self.client.get(self.list_url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        details = [r['equipment']['details'] for r in resp.data]
        logger.info(details)
        for detail in details:
            programs = detail.get('programs', [])
            self.assertTrue('windows' in programs and 'linux' in programs)

    def test_create_room_with_existing_fk_ids(self):
        payload = {
            "room_number": "R2",
            "capacity": 30,
            "building_id": self.b1.id,
            "equipment_id": self.e1.id
        }
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Room.objects.count(), 2)
        new_room = Room.objects.get(room_number="R2")
        self.assertEqual(new_room.building, self.b1)
        self.assertEqual(new_room.equipment, self.e1)

    def test_create_room_with_nested_and_get_or_create(self):

        payload = {
            "room_number": "R3",
            "capacity": 25,
            "building_data": {
                "name": "Nowy Budynek",
                "address": "ul. Nowa 5",
                "department": "X",
                "description": ""
            },
            "equipment_data": {
                "details": {"switches": 2, "computers": 4}
            }
        }
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Building.objects.filter(name="Nowy Budynek").exists())
        self.assertTrue(Equipment.objects.filter(details__computers=4).exists())
        self.assertEqual(Room.objects.filter(room_number="R3").count(), 1)

    def test_retrieve_room(self):
        resp = self.client.get(self.detail_url(self.room.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['room_number'], "R1")

    def test_update_room(self):
        resp = self.client.patch(self.detail_url(self.room.pk), {
            "capacity": 50
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.capacity, 50)

    def test_delete_room(self):
        resp = self.client.delete(self.detail_url(self.room.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Room.objects.filter(pk=self.room.pk).exists())
