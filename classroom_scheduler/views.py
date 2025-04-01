from django.http import HttpResponse


def home(request):
    return HttpResponse('Classroom scheduler home page')
