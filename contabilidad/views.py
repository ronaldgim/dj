from django.shortcuts import render
from warehouse.models import CuentasCobrar

# Create your views here.
def home(request):
    return render(request, 'contabilidad/home.html', {})


def lista_cuentas_por_cobrar(request):
    cuentas_cobrar = (
        CuentasCobrar.objects
            .using('gimpromed_sql')
            .all()
            .order_by('fecha_vencimiento')
        )
    context = {
        'cuentas_cobrar':cuentas_cobrar
    }
    return render(request, 'contabilidad/home.html', context)