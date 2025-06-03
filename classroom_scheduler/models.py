from django.db import models

from users.models import CustomUser


# Create your models here.
class Building(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    department = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    details = models.JSONField()

    def __str__(self):
        return f"Equipment #{self.pk}"


class Room(models.Model):
    building = models.ForeignKey(Building, related_name='rooms', on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, related_name='rooms', on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.PositiveIntegerField()
    room_number = models.CharField(max_length=50)

    def __str__(self):
        return f"Room {self.room_number} in {self.building.name}"


class ReservationInfo(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return f"Reservation for: {self.user_id}.\nDescription: {self.description}"


class Reservation(models.Model):
    room_id = models.ForeignKey(Room, on_delete=models.CASCADE)
    reservation_info_id = models.ForeignKey(ReservationInfo, on_delete=models.CASCADE)

    date_time = models.DateTimeField()

    def __str__(self):
        return f"Reservation for room {self.room_id}, description: {self.reservation_info_id}, date: {self.date_time}"
