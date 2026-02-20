from django.shortcuts import render, redirect
from warehouse.models import CuentasCobrar, Cliente
from contabilidad.models import ClienteExcluido
from django.views.decorators.http import require_POST
from django.contrib import messages


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
    return render(request, 'contabilidad/lista_cuentas_cobrar.html', context)


def lista_clientes_excluidos(request):
    
    clientes = Cliente.objects.using('gimpromed_sql').all()
    
    clientes_excluidos_list = list(
        ClienteExcluido.objects
        .values_list('codigo_cliente', flat=True)
    )
    
    clientes_excluidos = (
        Cliente.objects
        .using('gimpromed_sql')
        .filter(codigo_cliente__in=clientes_excluidos_list)
    )
    
    context = {
        'clientes': clientes,
        'clientes_excluidos': clientes_excluidos
    }
    
    return render(request, 'contabilidad/lista_clientes_excluidos.html', context)


@require_POST
def contabilidad_agregar_cliente_excluido(request):
    
    try:
        codigo_cliente = request.POST.get('codigo_cliente')
        
        ClienteExcluido.objects.create(
            codigo_cliente=codigo_cliente,
        )
        
        messages.success(request, 'Agregado correctamente')
        return redirect('clientes_excluidos')
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('clientes_excluidos')


@require_POST
def contabilidad_eliminar_cliente_excluido(request):
    
    try:
        codigo_cliente = request.POST.get('codigo_cliente')
        
        ClienteExcluido.objects.get(
            codigo_cliente=codigo_cliente,
        ).delete()
        
        messages.success(request, 'Eliminado correctamente')
        return redirect('clientes_excluidos')
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('clientes_excluidos')