from datetime import timedelta, datetime
from django.urls import reverse
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from django.contrib.auth import get_user_model

from users.models import CustomUser
from .models import Building, ClassGroup, Equipment, Reservation, ReservationInfo, Room
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
                               {'computers__gte': 10, 'switches__gte': 5, 'programs__contains': 'windows, linux'})
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

class ReservationTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='student', password='pass', email="email@em.pl")
        self.group = ClassGroup.objects.create(name="Group A")
        self.group.members.add(self.user)
        self.group.class_representatives.add(self.user)

        self.client.force_authenticate(self.user)

        self.building = Building.objects.create(
            name="Bldg1", address="Addr", department="Dept", description=""
        )
        self.equipment = Equipment.objects.create(details={'pc': 5})
        self.room = Room.objects.create(
            building=self.building,
            equipment=self.equipment,
            capacity=10,
            room_number="100"
        )
        
        self.room2 = Room.objects.create(
            building=self.building,
            equipment=self.equipment,
            capacity=15,
            room_number="101"
        )

        self.res_info = ReservationInfo.objects.create(
            user=self.user,
            group=self.group,
            description="Desc1"
        )

        self.res_info2 = ReservationInfo.objects.create(
            user=self.user,
            group=self.group,
            description="Desc2"
        )

        self.dt = timezone.now()
        self.res = Reservation.objects.create(
            room=self.room,
            reservation_info=self.res_info,
            date_time=self.dt
        )

        self.res2 = Reservation.objects.create(
            room=self.room,
            reservation_info = self.res_info,
            date_time=self.dt + timedelta(days=5)
        )

        self.res3 = Reservation.objects.create(
            room=self.room,
            reservation_info=self.res_info,
            date_time=self.dt + timedelta(days=10)
        )

        self.info_list = reverse('home_module:reservationinfo-list')
        self.info_detail = lambda pk: reverse('home_module:reservationinfo-detail', args=[pk])
        self.res_list = reverse('home_module:reservation-list')
        self.res_detail = lambda pk: reverse('home_module:reservation-detail', args=[pk])

    
    def test_list_reservation_info(self):
        resp = self.client.get(self.info_list)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_create_reservation_info(self):
        payload = {
            'user_id': self.user.id,
            'group_id': self.group.id,
            'description': 'New desc'
        }
        resp = self.client.post(self.info_list, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ReservationInfo.objects.filter(description='New desc').exists())

    def test_update_reservation_info(self):
        payload = {'description': 'Updated'}
        resp = self.client.patch(self.info_detail(self.res_info.id), payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.res_info.refresh_from_db()
        self.assertEqual(self.res_info.description, 'Updated')

    def test_doubled_reservation(self):
        before = Reservation.objects.count()
        time = timezone.now().isoformat()
        payload1 = {
            'room_id': self.room.id,
            'reservation_info_id': self.res_info.id,
            'date_time': time,
        }
        payload2 = {
            'room_id': self.room.id,
            'reservation_info_id': self.res_info2.id,
            'date_time': time,
        }
        resp1 = self.client.post(self.res_list, payload1, format='json')
        resp2 = self.client.post(self.res_list, payload2, format='json')

        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Reservation.objects.count(), before + 1)

    def test_delete_reservation_info(self):
        resp = self.client.delete(self.info_detail(self.res_info.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ReservationInfo.objects.filter(pk=self.res_info.id).exists())

    def test_list_reservations(self):
        resp = self.client.get(self.res_list)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['room']['room_number'], "100")
    
    def test_create_reservation(self):
        before = Reservation.objects.count()
        payload = {
            'room_id': self.room.id,
            'reservation_info_id': self.res_info.id,
            'date_time': (timezone.now() + timedelta(days=2)).isoformat()
        }
        resp = self.client.post(self.res_list, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), before + 1)

    def test_create_reservation_nested(self):
        before = Reservation.objects.count()
        payload = {
            'room_id': self.room.id,
            'reservation_info_data': {
                'user_id': self.user.id,
                'group_id': self.group.id,
                'description': "reservation_nested",
            },
            'date_time': (timezone.now() + timedelta(days=2)).isoformat()
        }
        resp = self.client.post(self.res_list, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), before + 1) 

    def test_retrieve_reservation(self):
        resp = self.client.get(self.res_detail(self.res.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['reservation_info']['description'], "Desc1")

    def test_delete_reservation(self):
        resp = self.client.delete(self.res_detail(self.res.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reservation.objects.filter(pk=self.res.id).exists())

    def test_filter_by_date_range(self):
        start = self.dt.isoformat()
        end = (self.dt + timedelta(days=6)).isoformat()

        resp = self.client.get(self.res_list, {
            'date_time__gte': start,
            'date_time__lte': end
        })

        self.assertEqual(resp.status_code, 200)
        returned_ids = {res['id'] for res in resp.data}
        expected_ids = {self.res.id, self.res2.id}

        self.assertEqual(returned_ids, expected_ids)

    def test_bulk_create_reservations(self):
        res_count = Reservation.objects.count() 
        now = timezone.now()
        payload = {
            "room_id": self.room2.id,
            "reservation_info_id": self.group.id,
            "date_times": [
                (now + timezone.timedelta(days=1)).isoformat(),
                (now + timezone.timedelta(days=2)).isoformat(),
                (now + timezone.timedelta(days=3)).isoformat(),
            ]
        }
    
        resp= self.client.post(reverse("home_module:reservation-bulk-create-reservation"), data=payload, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Reservation.objects.count(), res_count + 3)
    
    def test_bulk_create_reservations_nested(self):
        res_count = Reservation.objects.count()
        now = timezone.now()
        payload = {
            "room_id": self.room2.id,
            "reservation_info_data": {
                'user_id': self.user.pk,
                'group_id': self.group.pk,
                'description': "teststat",
            },
            "date_times": [
                (now + timezone.timedelta(days=4)).isoformat(),
                (now + timezone.timedelta(days=5)).isoformat(),
                (now + timezone.timedelta(days=6)).isoformat(),
            ]
        }
    
        resp= self.client.post(reverse("home_module:reservation-bulk-create-reservation"), data=payload, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Reservation.objects.count(), res_count + 3)

    def test_bulk_create_reservations_failed(self):
        res_count = Reservation.objects.count() 
        now = timezone.now()
        payload = {
            "room_id": self.room2.id,
            "reservation_info_id": self.res_info.id,
            "date_times": [
                (now + timezone.timedelta(days=10)).isoformat(),
                (now + timezone.timedelta(days=10)).isoformat(),
                (now + timezone.timedelta(days=10)).isoformat(),
            ]
        }
        resp= self.client.post(reverse("home_module:reservation-bulk-create-reservation"), data=payload, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Reservation.objects.count(), res_count)

class RoomAvailableAPITest(APITestCase):
    def setUp(self):
        # Setup user (wymagany do ReservationInfo)
        self.user = CustomUser.objects.create_user(username='testuser', email='test@example.com', password='testpass')

        # Optional group
        self.group = ClassGroup.objects.create(name="Test Group")
        self.group.members.add(self.user)

        # Setup ReservationInfo
        self.reservation_info = ReservationInfo.objects.create(
            user=self.user,
            group=self.group,
            description="Test reservation"
        )

        # Setup building
        self.building = Building.objects.create(
            name="Engineering Hall",
            address="123 Main St",
            department="Engineering"
        )

        # Setup equipment with sufficient attributes
        self.equipment_good = Equipment.objects.create(details={
            "windows": 2,
            "whiteboard": 3,
            "projector": True
        })

        # Setup equipment that doesn't match filter
        self.equipment_bad = Equipment.objects.create(details={
            "windows": 0,
            "whiteboard": 1
        })

        # Room that should match
        self.room_matching = Room.objects.create(
            building=self.building,
            equipment=self.equipment_good,
            capacity=35,
            room_number="A101"
        )

        # Room that shouldn't match (bad equipment)
        self.room_non_matching = Room.objects.create(
            building=self.building,
            equipment=self.equipment_bad,
            capacity=40,
            room_number="B202"
        )

        # Room that should be excluded due to reservation
        self.reserved_room = Room.objects.create(
            building=self.building,
            equipment=self.equipment_good,
            capacity=50,
            room_number="C303"
        )

        self.overlapping_start = make_aware(datetime(2025, 6, 17, 6, 30))
        Reservation.objects.create(
            room=self.reserved_room,
            date_time=self.overlapping_start,
            reservation_info=self.reservation_info
        )

    def test_rooms_available_with_filters(self):
        url = '/api/rooms/available/'
        params = {
            'start': '2025-06-17T06:00:00.000Z',
            'end': '2025-06-17T07:30:00.000Z',
            'capacity__gte': 30,
            'windows__gte': 1,
            'whiteboard__gte': 2
        }

        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)

        room_ids = [room['id'] for room in response.data]
        self.assertIn(self.room_matching.id, room_ids)
        self.assertNotIn(self.room_non_matching.id, room_ids)
        self.assertNotIn(self.reserved_room.id, room_ids)
