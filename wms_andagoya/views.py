from django.shortcuts import render

# Create your views here.
def wms_andagoya_home(request):
    return render(request, 'wms_andagoya/home.html', {})