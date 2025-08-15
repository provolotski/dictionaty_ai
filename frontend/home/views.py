from django.shortcuts import render
from django.http import HttpResponse

def home_page(request):
    return render(request, 'home.html')

def search_page(request):
    return render(request, 'search.html')

def dictionaries_page(request):
    return render(request, 'dictionaries.html')

def import_page(request):
    return render(request, 'import.html')

def export_page(request):
    return render(request, 'export.html')

def analytics_page(request):
    return render(request, 'analytics.html')