from django.db import models


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