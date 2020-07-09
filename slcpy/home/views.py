from django.utils import timezone
from django.shortcuts import render


def home(request):
    ctx = {}
    template = "home/index.html"
    ctx = {
        'next_meetup': {
            'date': timezone.datetime(2020, 7, 8, 17, 30)
        }
    }
    return render(request, template, ctx)
