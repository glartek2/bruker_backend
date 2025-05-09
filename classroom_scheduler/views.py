from django.shortcuts import render


def home(request):
    return render(request, 'homepage.html')



from django.http import HttpResponse

from django.urls import reverse_lazy
from django.views import generic
from .models import Building, Room, Equipment


def home(request):
    return HttpResponse('Classroom scheduler home page')


# Buildings
class BuildingListView(generic.ListView):
    model = Building


#class BuildingDetailView(generic.DetailView):
#    model = Building


class BuildingCreateView(generic.CreateView):
    model = Building
    fields = ['name','address','department','description']
    success_url = reverse_lazy('building-list')


class BuildingUpdateView(generic.UpdateView):
    model = Building
    fields = ['name','address','department','description']
    success_url = reverse_lazy('building-list')


class BuildingDeleteView(generic.DeleteView):
    model = Building
    success_url = reverse_lazy('building-list')


# Rooms
class RoomListView(generic.ListView):
    model = Room


#class RoomDetailView(generic.DetailView):
#    model = Room


class RoomCreateView(generic.CreateView):
    model = Room
    fields = ['building','equipment','capacity','room_number']
    success_url = reverse_lazy('room-list')


class RoomUpdateView(generic.UpdateView):
    model = Room
    fields = ['building','equipment','capacity','room_number']
    success_url = reverse_lazy('room-list')


class RoomDeleteView(generic.DeleteView):
    model = Room
    success_url = reverse_lazy('room-list')


# Equipment
class EquipmentListView(generic.ListView):
    model = Equipment


#class EquipmentDetailView(generic.DetailView):
#    model = Equipment


class EquipmentCreateView(generic.CreateView):
    model = Equipment
    fields = ['details']
    success_url = reverse_lazy('equipment-list')


class EquipmentUpdateView(generic.UpdateView):
    model = Equipment
    fields = ['details']
    success_url = reverse_lazy('equipment-list')


class EquipmentDeleteView(generic.DeleteView):
    model = Equipment
    success_url = reverse_lazy('equipment-list')

