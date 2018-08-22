from django.shortcuts import render


def home(request):
    ctx = {}
    template = "home/index.html"
    return render(request, template, ctx)
