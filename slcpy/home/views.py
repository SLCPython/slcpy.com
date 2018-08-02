from django.shortcuts import render


def home(request):
    ctx = {}
    template_name = "home/index.html"
    return render(request, template_name, ctx)
