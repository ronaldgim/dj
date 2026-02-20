from django.shortcuts import render, redirect
from warehouse.models import CuentasCobrar, Cliente
from contabilidad.models import ClienteExcluido, NotificacionCartera
from django.views.decorators.http import require_POST
from django.contrib import messages
from datetime import datetime
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.db.models import Sum, Case, When, DecimalField, Value
from django.template.loader import render_to_string

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


def lista_notificaciones(request):
    
    notificaciones = NotificacionCartera.objects.select_related('usuario').all()
    lista_clientes = list(notificaciones.values_list('codigo_cliente', flat=True))
    clientes = Cliente.objects.using('gimpromed_sql').filter(codigo_cliente__in=lista_clientes)
    clientes_dict = {c.codigo_cliente:c for c in clientes}
    
    notificaciones_data = []
    for i in notificaciones:
        cli = clientes_dict.get(i.codigo_cliente)
        notificaciones_data.append({
            'id':i.id,
            'cliente':cli.nombre_cliente,
            'ruc':cli.identificacion_fiscal,
            'correos':i.correos,
            'errores':i.errores if i.errores else '-',
            'usuario': f'{i.usuario.first_name} {i.usuario.last_name}' if i.usuario else i.usuario_auto,
            'fecha_hora': i.creado.strftime('%Y-%m-%d %H:%M')
        })
    
    context = {
        'notificaciones':notificaciones_data
    }
    
    return render(request, 'contabilidad/lista_notificaciones.html', context)


def nueva_notificacion(request):

    # 1. Clientes excluidos (DB local)
    clientes_excluidos = set(
        ClienteExcluido.objects.values_list('codigo_cliente', flat=True)
    )

    # 2. Clientes con cartera (DB externa)
    cuentas_cobrar_clientes = (
        CuentasCobrar.objects
        .using('gimpromed_sql')
        .exclude(codigo_cliente__in=clientes_excluidos)
        .values_list('codigo_cliente', flat=True)
        .distinct()
    )

    clientes = (
        Cliente.objects
        .using('gimpromed_sql')
        .filter(codigo_cliente__in=cuentas_cobrar_clientes)
    )

    cli = request.GET.get('codigo_cliente')

    context = {
        'clientes': clientes,
    }

    if cli:
        hoy = datetime.now().date()

        # Cliente seleccionado
        cliente = Cliente.objects.using('gimpromed_sql').get(codigo_cliente=cli)

        # Facturas
        facturas = (
            CuentasCobrar.objects
            .using('gimpromed_sql')
            .filter(codigo_cliente=cli)
        )

        # ==============================
        # CLASIFICACIÓN
        # ==============================
        facturas_vigentes = []
        facturas_vencidas = []

        for f in facturas:
            dias = (hoy - f.fecha_vencimiento).days

            item = {
                'numero': f.numero_factura,
                'fecha_emision': f.fecha_factura,
                'valor_total': f.valor_total_pagado,
                'pagado': f.valor_total_pagado,
                'retencion': 0,  # ajusta si tienes campo real
                'credito': 0,    # ajusta si tienes campo real
                'saldo': f.balance,
                'fecha_vencimiento': f.fecha_vencimiento,
            }

            if f.fecha_vencimiento >= hoy:
                item['dias_vigente'] = abs(dias)
                facturas_vigentes.append(item)
            else:
                item['dias_vencido'] = dias
                facturas_vencidas.append(item)

        # TOTALES
        totales = facturas.aggregate(
            total_vigente=Coalesce(
                Sum(
                    Case(
                        When(fecha_vencimiento__gte=hoy, then='balance'),
                        output_field=DecimalField()
                    )
                ),
                Value(0, output_field=DecimalField())
            ),
            total_vencido=Coalesce(
                Sum(
                    Case(
                        When(fecha_vencimiento__lt=hoy, then='balance'),
                        output_field=DecimalField()
                    )
                ),
                Value(0, output_field=DecimalField())
            ),
            total_cartera=Coalesce(
                Sum('balance'),
                Value(0, output_field=DecimalField())
            )
        )

        # AGING (RESUMEN)
        resumen = {
            'vigente': 0,
            'rango_1_30': 0,
            'rango_31_60': 0,
            'rango_61_90': 0,
            'rango_91': 0,
        }

        for f in facturas:
            dias = (hoy - f.fecha_vencimiento).days
            saldo = f.balance or 0

            if dias <= 0:
                resumen['vigente'] += saldo
            elif 1 <= dias <= 30:
                resumen['rango_1_30'] += saldo
            elif 31 <= dias <= 60:
                resumen['rango_31_60'] += saldo
            elif 61 <= dias <= 90:
                resumen['rango_61_90'] += saldo
            else:
                resumen['rango_91'] += saldo

        # CONTEXTO PARA TEMPLATE EMAIL  
        email_context = {
            'cliente_nombre': cliente.nombre_cliente,
            'cartera_vencida': totales['total_vencido'],
            'facturas_vencidas': facturas_vencidas,
            'facturas_vigentes': facturas_vigentes,
            'total_vigentes': totales['total_vigente'],
            'total_cartera': totales['total_cartera'],
            'resumen': resumen,
        }

        # Render HTML del correo
        correo_html = render_to_string(
            'emails/cuentas_cobrar.html',
            email_context
        )

        # Agregar al context principal
        context.update({
            'cliente_selected': cliente,
            'correo_html': correo_html,
            **email_context
        })

    return render(request, 'contabilidad/nueva_notificacion.html', context)


def crear_correo_notificacion(codigo_cliente):
    pass