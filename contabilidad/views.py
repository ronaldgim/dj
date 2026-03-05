from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from warehouse.models import CuentasCobrar, Cliente, VendedorMBA
from contabilidad.models import ClienteExcluido, NotificacionCartera
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from datetime import datetime
from django.http import JsonResponse
from decimal import Decimal
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from contabilidad.forms import NotificacionCarteraForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# Services
from contabilidad.services import CarteraKPIService


@login_required(login_url='login')
def lista_cuentas_por_cobrar(request):

    cli = request.GET.get('codigo_cliente')

    base_qs = (
        CuentasCobrar.objects
        .using('gimpromed_sql')
        # .only(
        #     'codigo_cliente',
        #     'nombre_cliente',
        #     'fecha_vencimiento',
        #     'valor_total_saldo_a_cobrar',
        #     'valor_total_pagado',
        #     'limite_credito',
        #     'balance'
        # )
    )

    # Clientes únicos (para filtro)
    clientes = (
        base_qs
        .values('codigo_cliente', 'nombre_cliente')
        .distinct()
        .order_by('nombre_cliente')
    )

    # Query principal
    qs = base_qs.order_by('fecha_vencimiento')

    cliente = None
    if cli:
        qs = qs.filter(codigo_cliente=cli)
        cliente = Cliente.objects.using('gimpromed_sql').get(codigo_cliente=cli)

    # KPIs
    kpi_service = CarteraKPIService(qs)
    kpis = kpi_service.get_all_kpis()

    context = {
        'clientes': clientes,
        'cliente':cliente,
        'cuentas_cobrar': qs,
        'kpis': kpis
    }

    return render(request, 'contabilidad/lista_cuentas_cobrar.html', context)


@login_required(login_url='login')
def lista_clientes_excluidos(request):
    
    clientes = (
        Cliente.objects
        .using('gimpromed_sql')
        .all()
        .order_by('nombre_cliente')
    )
    
    clientes_excluidos_list = list(
        ClienteExcluido.objects
        .values_list('codigo_cliente', flat=True)
    )
    
    clientes_excluidos = (
        Cliente.objects
        .using('gimpromed_sql')
        .filter(codigo_cliente__in=clientes_excluidos_list)
        .order_by('-id')
    )
    
    context = {
        'clientes': clientes,
        'clientes_excluidos': clientes_excluidos
    }
    
    return render(request, 'contabilidad/lista_clientes_excluidos.html', context)


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
def lista_notificaciones(request):
    
    notificaciones = NotificacionCartera.objects.select_related('usuario').all().order_by('-id')
    lista_clientes = list(notificaciones.values_list('codigo_cliente', flat=True))
    clientes = Cliente.objects.using('gimpromed_sql').filter(codigo_cliente__in=lista_clientes)
    clientes_dict = {c.codigo_cliente:c for c in clientes}
    
    notificaciones_data = []
    for i in notificaciones:
        cli = clientes_dict.get(i.codigo_cliente)
        notificaciones_data.append({
            'id':i.id,
            'enum':i.enum,
            'cliente':cli.nombre_cliente,
            'ruc':cli.identificacion_fiscal,
            'correos':i.correos,
            'errores':i.errores if i.errores else '-',
            'usuario': f'{i.usuario.first_name} {i.usuario.last_name}' if i.usuario else i.usuario_auto,
            'fecha_hora': i.creado.strftime('%Y-%m-%d %H:%M'),
            # 'correo_text':i.correo_text
        })
    
    context = {
        'notificaciones':notificaciones_data
    }
    
    return render(request, 'contabilidad/lista_notificaciones.html', context)


def cartera_vencida_por_cliente(codigo_cliente):
    
    hoy = datetime.now().date()

    cliente = (
        Cliente.objects
        .using('gimpromed_sql')
        .get(codigo_cliente=codigo_cliente)
    )

    facturas = list(
        CuentasCobrar.objects
        .using('gimpromed_sql')
        .filter(codigo_cliente=codigo_cliente)
    )

    facturas_vigentes = []
    facturas_vencidas = []

    resumen = {
        'vigente': Decimal('0'),
        'rango_1_30': Decimal('0'),
        'rango_31_60': Decimal('0'),
        'rango_61_90': Decimal('0'),
        'rango_91': Decimal('0'),
    }

    tot_vencidas = {
        'valor': Decimal('0'),
        'pagado': Decimal('0'),
        'retencion': Decimal('0'),
        'credito': Decimal('0'),
        'saldo': Decimal('0'),
    }

    tot_vigentes = {
        'valor': Decimal('0'),
        'pagado': Decimal('0'),
        'retencion': Decimal('0'),
        'credito': Decimal('0'),
        'saldo': Decimal('0'),
    }

    # ==============================
    # LOOP PRINCIPAL
    # ==============================
    for f in facturas:
        dias = (hoy - f.fecha_vencimiento).days

        valor = f.valor_factura or Decimal('0')
        pagado = f.valor_total_pagado or Decimal('0')
        retencion = f.valor_retencion or Decimal('0')
        credito = getattr(f, 'valor_total_descuento', Decimal('0')) or Decimal('0')
        saldo = f.valor_total_saldo_a_cobrar or Decimal('0')

        item = {
            'numero': f.numero_factura,
            'fecha_emision': f.fecha_factura,
            'valor': valor,
            'pagado': pagado,
            'retencion': retencion,
            'credito': credito,
            'saldo': saldo,
            'fecha_vencimiento': f.fecha_vencimiento,
        }

        if dias <= 0:
            item['dias_vigente'] = abs(dias)
            facturas_vigentes.append(item)

            resumen['vigente'] += saldo

            tot_vigentes['valor'] += valor
            tot_vigentes['pagado'] += pagado
            tot_vigentes['retencion'] += retencion
            tot_vigentes['credito'] += credito
            tot_vigentes['saldo'] += saldo

        else:
            item['dias_vencido'] = dias
            facturas_vencidas.append(item)

            tot_vencidas['valor'] += valor
            tot_vencidas['pagado'] += pagado
            tot_vencidas['retencion'] += retencion
            tot_vencidas['credito'] += credito
            tot_vencidas['saldo'] += saldo

            if dias <= 30:
                resumen['rango_1_30'] += saldo
            elif dias <= 60:
                resumen['rango_31_60'] += saldo
            elif dias <= 90:
                resumen['rango_61_90'] += saldo
            else:
                resumen['rango_91'] += saldo

    # ORDENAR (IMPORTANTE)
    facturas_vencidas.sort(key=lambda x: x['dias_vencido'], reverse=True)

    #  GRADIENTE (AQUÍ VA)
    total = len(facturas_vencidas) or 1

    for index, item in enumerate(facturas_vencidas):
        ratio = index / (total - 1 or 1)

        if ratio < 0.5:
            t = ratio / 0.5
            r = 255
            g = int(99 + (255 - 99) * t)
            b = int(71 + (150 - 71) * t)
        else:
            t = (ratio - 0.5) / 0.5
            r = 255
            g = 255
            b = int(150 + (255 - 150) * t)

        item['bg_color'] = f"rgb({r},{g},{b})"

    # TOTALES
    totales = {
        'total_vigente': resumen['vigente'],
        'total_vencido': tot_vencidas['saldo'],
        'total_cartera': sum(resumen.values())
    }

    email_context = {
        'cliente_nombre': cliente.nombre_cliente,
        'cartera_vencida': totales['total_vencido'],

        'facturas_vencidas': facturas_vencidas,
        'facturas_vigentes': facturas_vigentes,

        'tot_vencidas': tot_vencidas,
        'tot_vigentes': tot_vigentes,

        'total_vigentes': totales['total_vigente'],
        'total_cartera': totales['total_cartera'],
        'resumen': resumen,
    }

    correo_html = render_to_string(
        'emails/cuentas_cobrar.html',
        email_context
    )

    return {
        'correo_html': correo_html,
        'email_context': email_context
    }


@login_required(login_url='login')
@require_GET
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
        .order_by('nombre_cliente')
    )

    cli = request.GET.get('codigo_cliente')

    context = {
        'clientes': clientes,
    }

    if cli:
        
        correo_data = cartera_vencida_por_cliente(cli)
        cliente = (
            Cliente.objects
            .using('gimpromed_sql')
            .get(codigo_cliente=cli)
        )
        
        asesor = VendedorMBA.objects.using('gimpromed_sql').filter(code=cliente.salesman).first()
        
        # Agregar al context principal
        context.update({
            'cliente_selected': cliente,
            'asesor':asesor,
            'dep_financiero':'dreyes@gimpromed.com',
            'correo_html': correo_data.get('correo_html'),
            **correo_data.get('email_context')
        })

    return render(request, 'contabilidad/nueva_notificacion.html', context)


def obtener_lista_correos(correos_str, correos_extra=None):
    """
    Convierte un string de correos separados por coma en una lista válida,
    limpia duplicados y agrega correos extra desde backend.
    """

    if not correos_str:
        correos_str = ""

    # Separar y limpiar
    lista = [c.strip() for c in correos_str.split(",") if c.strip()]

    # Agregar correos extra (backend)
    if correos_extra:
        lista.extend(correos_extra)

    # Eliminar duplicados
    lista = list(set(lista))

    # Validar correos
    correos_validos = []
    correos_invalidos = []

    for correo in lista:
        try:
            validate_email(correo)
            correos_validos.append(correo)
        except ValidationError:
            correos_invalidos.append(correo)

    if correos_invalidos:
        raise ValidationError(f"Correos inválidos: {', '.join(correos_invalidos)}")

    return correos_validos


@login_required(login_url='login')
@require_POST
def crear_notificacion(request):
    
    try:
        correos_input_post = request.POST.get('correos')
        if not correos_input_post:
            messages.error(request, 'Correo de cliente son requeridos !!!')
            return redirect('nueva_notificacion')
        
        asesor_email = request.POST.get('asesor_email')
        dep_financiero_email = request.POST.get('dep_financiero_email')

        emails_cc = []
        if asesor_email and asesor_email != 'info@gimpromed.com':
            emails_cc.append(asesor_email)
        if dep_financiero_email:
            emails_cc.append(dep_financiero_email)

        # eliminar duplicados (por si acaso)
        emails_cc = list(set(emails_cc))
        
        form = NotificacionCarteraForm(request.POST)
        
        if form.is_valid():
            notificacion = form.save(commit=False)
            
            # Asignar usuario desde backend (NO desde el form)
            notificacion.usuario = request.user
            
            # Generar el correo en backend (NO confiar en hidden input)
            codigo_cliente = form.cleaned_data['codigo_cliente']
            notificacion.correo_text = cartera_vencida_por_cliente(codigo_cliente).get('correo_html')
            
            # (opcional) usuario automático
            # notificacion.usuario_auto = request.user.username
            
            # Correos
            correos_input = form.cleaned_data['correos']            
            lista_correos_cliente = obtener_lista_correos(correos_input)
            
            notificacion.save()
            
            if notificacion.id:
                
                try:
                    # CREAR CORREO
                    correo = EmailMultiAlternatives(
                        subject    = "Cartera vencida",
                        from_email = settings.DEFAULT_FROM_EMAIL,
                        to         = lista_correos_cliente,
                        cc         = emails_cc
                    )
                    correo.attach_alternative(notificacion.correo_text, "text/html")
                    
                    # ENVIAR
                    correo.send(fail_silently=False)
                    messages.success(request, 'Correo enviado correctamente !!!')
                    return redirect('lista_notificaciones')
                
                except Exception as e:
                    notificacion.errores = str(e)
                    notificacion.save()
                    messages.error(request, f'Error al enviar el correo: {e}')
                    return redirect('lista_notificaciones')
        
        return redirect('nueva_notificacion')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('nueva_notificacion')


@login_required(login_url='login')
@require_GET
def detalle_notificacion(request, id):
    
    notificacion = NotificacionCartera.objects.get(id=id)
    cliente = Cliente.objects.using('gimpromed_sql').get(codigo_cliente=notificacion.codigo_cliente)
    
    context = {
        'notificacion':notificacion,
        'cliente':cliente
    }
    
    return render(request, 'contabilidad/detalle_notificacion.html', context)