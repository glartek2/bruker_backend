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
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reservations')
    class_representatives = models.ManyToManyField(CustomUser, related_name='represented_reservations')
    description = models.TextField()

    def __str__(self):
        return f"Reservation for: {self.user}.\nDescription: {self.description}"


class Reservation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    reservation_info = models.ForeignKey(ReservationInfo, on_delete=models.CASCADE)

    date_time = models.DateTimeField()
    proposed_date_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reservation for room {self.room}, description: {self.reservation_info}, date: {self.date_time}"
