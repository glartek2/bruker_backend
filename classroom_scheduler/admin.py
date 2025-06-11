from django.contrib import admin
from .models import ClassGroup, Room, Reservation, ReservationInfo, Equipment, Building
# Register your models here.

admin.site.register(ClassGroup)
admin.site.register(Room)
admin.site.register(Equipment)
admin.site.register(Building)
admin.site.register(Reservation)
admin.site.register(ReservationInfo)