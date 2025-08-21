# DB
from django.db import connections

# Shortcuts
from django.shortcuts import redirect, render

# Models
from carta.models import (
    CartaGeneral, 
    CartaProcesos, 
    CartaItem, 
    AnularCartaGeneral, 
    AnularCartaProcesos,
    AnularCartaItem
    )


# Form
from carta.forms import (
    CartaGeneralForm, 
    CartaProcesosForm, 
    CartaItemForm, 
    AnularCartaGeneralForm, 
    AnularCartaProcesosForm,
    AnularCartaItemForm
    )

# Generic View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

# PDF
from django_xhtml2pdf.views import PdfMixin

# LoginRequired
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required

# Permisos
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

# Messages
from django.contrib import messages

# Url
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

# Django products
from datos.views import productos_odbc_and_django, de_dataframe_a_template

import ast
import pandas as pd

# Clientes
def tabla_clientes(ruc):
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM clientes WHERE IDENTIFICACION_FISCAL = %s", [ruc])
        columns = [col[0] for col in cursor.description]
        clientes = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return clientes


# Carta General
@login_required(login_url='login')
def carta_general(request):

    if not request.user.has_perm('carta.add_cartageneral'):
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('list')

    ''' Llenar campos de carga general y crear objeto '''
    form = CartaGeneralForm()
    
    context = {
        'form':form,
    }
    
    cliente = request.GET.get('buscar_cliente')
    if cliente:        
        ruc = str(cliente)                
        cliente_dict = tabla_clientes(ruc) 
        if cliente_dict:
            identificacion_fiscal = cliente_dict[0].get('IDENTIFICACION_FISCAL')
            nombre_cliente = cliente_dict[0].get('NOMBRE_CLIENTE')
            
            context = {
                'ruc':identificacion_fiscal, 
                'nombre_cliente':nombre_cliente, 
                'form':form,
            }
        else:
            context = {
                'form':form,
                'error':'El Ruc no coincide con ningun cliente, por favor intente nuevamente!!!'
            }

    if request.method == 'POST':
        
        try: 
            form = CartaGeneralForm(request.POST)
            
            if form.is_valid():
                # form.save()
                return redirect('general_list')
            else:
                messages.error(request, f"Error {form.errors}")
    
        except Exception as e:
            messages.error(request, f"Error {e}")

    return render(request, 'cartas/carta_general/new.html', context)


class CartaGeneralPDF(PermissionRequiredMixin, LoginRequiredMixin, PdfMixin ,DetailView):
    ''' Detail view o pdf view de carga general creada '''
    model = CartaGeneral
    template_name = 'cartas/carta_general/detail.html'

    permission_required = 'carta.add_cartageneral'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('general_list'))


class CartaGeneralList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    ''' Lista de cartas generales creadas '''
    model = CartaGeneral
    queryset = CartaGeneral.objects.filter(anularcartageneral__isnull=True)
    template_name = 'cartas/carta_general/list_general.html'
    ordering = ['-pk']

    permission_required = 'carta.view_cartageneral'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('inicio'))


@login_required(login_url='login')
def anular_cartageneral(request, slug):

    if request.user.has_perm('carta.add_anularcartageneral'):

        carta = CartaGeneral.objects.get(slug=slug).pk
        form = AnularCartaGeneralForm({
            'cartageneral':carta
        })

        carta_view = CartaGeneral.objects.get(slug=slug)
        
        context = {
            'form': form,
            'carta': carta,
            'carta_view': carta_view,
        }

        if request.method == 'POST':
            form = AnularCartaGeneralForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('anular_general_list')
            
            else:
                messages.error(request, f'Error {form.errors} !!!')

    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/cartas/general/list')
    
    return render(request, 'cartas/carta_general/anular_cartageneral.html', context)


class CartaGeneralAnuladasList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    ''' Listado de cartas generales anuladas '''
    model = AnularCartaGeneral
    queryset = AnularCartaGeneral.objects.all()
    template_name = 'cartas/carta_general/list_general_anulada.html'
    ordering = ['-pk']

    permission_required = 'carta.view_anularcartageneral'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('general_list'))


class CartaGeneralAnuladaDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = AnularCartaGeneral
    template_name = 'cartas/carta_general/anular_cartageneral_detail.html'

    permission_required = 'carta.view_anularcartageneral'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('general_list'))


# # Carta Procesos
# @login_required(login_url='login')
# def carta_procesos(request):
#     ''' Llenar campos de carga general y crear objeto '''
#     form = CartaProcesosForm()
    
#     context = {
#         'form':form,
#     }
    
#     if request.user.has_perm('carta.add_cartaprocesos'):

#         try:
#             if request.method == 'GET':
#                 ruc = request.GET['buscar_cliente']
#                 ruc = str(ruc)
                
#                 cliente_dict = tabla_clientes(ruc)[0]
#                 identificacion_fiscal = cliente_dict.get('IDENTIFICACION_FISCAL')
#                 nombre_cliente = cliente_dict.get('NOMBRE_CLIENTE')
#                 if identificacion_fiscal == '':
#                     context = {
#                         'error':'El Ruc no coincide con ningun cliente, por favor intente nuevamente!!!'
#                     }
#                 else:
#                     context = {
#                         'ruc':identificacion_fiscal, 
#                         'nombre_cliente':nombre_cliente, 
#                         'form':form,
#                     }

#             elif request.method == 'POST':
                    
#                 form = CartaProcesosForm(request.POST)
                
#                 if form.is_valid():
#                     #form.save()
#                     return redirect('procesos_list')
#                 else:
#                     messages.error(request, f'Error {form.errors} !!!')
#             else:

#                 context = {
#                     'form':form,
#                     'errors':form.errors                        
#                 }
        
#         except Exception as e:
#             print(e)
#             messages.error(request, f'Error {e} !!!')
#     else:
#         messages.error(request, 'No tienes los permisos necesarios !!!')
#         return HttpResponseRedirect('list')
        
#     return render(request, 'cartas/carta_procesos/new.html', context)

# Función auxiliar para buscar cliente
from django.http import JsonResponse
def buscar_cliente_por_ruc_ajax(request):
    """
    Busca un cliente por su RUC y devuelve un diccionario con los datos.
    """
    ruc = request.POST.get('ruc')
    
    try:
        resultado = tabla_clientes(ruc)
        if resultado:
            return JsonResponse({'ruc':resultado[0]})  # Retorna el primer cliente encontrado
        return None
    except Exception as e:
        print(f'Error al buscar cliente: {e}')
        return None
    

@login_required(login_url='login')
def carta_procesos(request):
    """
    Vista para manejar la creación de un objeto CartaProcesos.
    """
    # Validar permisos
    if not request.user.has_perm('carta.add_cartaprocesos'):
        messages.error(request, 'No tienes los permisos necesarios para realizar esta acción.')
        return redirect('procesos_list')

    # Inicializar formulario y contexto
    form = CartaProcesosForm()
    context = {'form': form}

    if request.method == 'POST':
        form = CartaProcesosForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'La carta por procesos se creó correctamente.')
                return redirect('procesos_list')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al guardar: {e}')
        else:
            messages.error(request, f'Error en el formulario: {form.errors}')

    return render(request, 'cartas/carta_procesos/new.html', context)



class CartaProcesosPDF(PermissionRequiredMixin, LoginRequiredMixin, PdfMixin ,DetailView):
    ''' Detail view o pdf view de carga general creada '''
    model = CartaProcesos
    template_name = 'cartas/carta_procesos/detail.html'

    permission_required = 'carta.add_cartaprocesos'
 
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('procesos_list'))


class CartaProcesosList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    ''' Lista de cartas generales creadas '''
    model = CartaProcesos
    queryset = CartaProcesos.objects.filter(anularcartaprocesos__isnull=True)
    template_name = 'cartas/carta_procesos/list_procesos.html'
    ordering = ['-pk']

    permission_required = 'carta.view_cartaprocesos'
 
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('procesos_list'))


@login_required(login_url='login')
def anular_cartaprocesos(request, slug):

    if request.user.has_perm('carta.add_anularcartaprocesos'):

        carta = CartaProcesos.objects.get(slug=slug)
        form  = AnularCartaProcesosForm({
        'cartaprocesos':carta.pk
        })

        context = {
            'form':form,
            'carta':carta,
        }
        
        if request.method == 'POST':
            form = AnularCartaProcesosForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('anular_procesos_list')
            else:
                messages.error(request, f'Error {form.errors} !!!')
    
    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/cartas/procesos/list')

    return render(request, 'cartas/carta_procesos/anular_cartaprocesos.html', context)


class AnularCartaProcesosList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    
    model = AnularCartaProcesos
    template_name = 'cartas/carta_procesos/list_procesos_anuladas.html'
    ordering = ['-pk']
    permission_required = 'carta.view_anularcartaprocesos'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('procesos_list'))


class CartaProcesosAnuladaDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = AnularCartaProcesos
    template_name = 'cartas/carta_procesos/anular_cartaprocesos_detail.html'
    
    permission_required = 'carta.view_anularcartaprocesos'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('procesos_list'))


@login_required(login_url='login')
def carta_items(request):
    """
    Vista para manejar la creación de un objeto CartaItems.
    """
    # Validar permisos
    if not request.user.has_perm('carta.add_cartaitem'):
        messages.error(request, 'No tienes los permisos necesarios para realizar esta acción.')
        return redirect('items_list')

    # Inicializar formulario y contexto
    form = CartaItemForm()
    productos_mba = productos_odbc_and_django().drop_duplicates()[['product_id','Nombre','MarcaDet']]
    productos_mba['nombre_completo'] = productos_mba['product_id'] + ' - ' + productos_mba['Nombre'] + ' - ' + productos_mba['MarcaDet']
    
    context = {
        'form': form,
        'productos_mba': de_dataframe_a_template(productos_mba)
        }

    if request.method == 'POST':
        
        # Copia el QueryDict y hazlo mutable temporalmente
        data = request.POST.copy()
        form = CartaItemForm(data)
        
        # Obtener la lista y transformarla como necesites
        p_mba = request.POST.getlist('items_mba')
        p_mba = dict(enumerate(p_mba))  # Convierte a diccionario enumerado
        p_mba = str(p_mba)  # Convierte a string (si es necesario)

        # Agrega el nuevo campo al QueryDict mutable
        data['items_mba'] = p_mba
        
        # Usa el nuevo QueryDict en el formulario
        form = CartaItemForm(data)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'La carta por items se creó correctamente.')
                return redirect('items_list')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al guardar: {e}')
        else:
            messages.error(request, f'Error en el formulario: {form.errors}')

    return render(request, 'cartas/carta_items/new.html', context)


class CartaItemsPDF(PermissionRequiredMixin, LoginRequiredMixin, PdfMixin ,DetailView):
    ''' Detail view o pdf view de carga general creada '''
    model = CartaItem
    template_name = 'cartas/carta_items/detail.html'
    permission_required = 'carta.add_cartaitem'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('items_list'))
    
    #  añadir un contexto adicional
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # obtener el valor items_mba de la base de datos del detial
        items_mba_completo = self.object.items_mba
        
        if items_mba_completo:
            items_mba_completo = ast.literal_eval(items_mba_completo)
            df = pd.DataFrame(list(items_mba_completo.items()), columns=['index', 'product_id'])
            df = df.merge(productos_odbc_and_django()[['product_id','Nombre','MarcaDet']], on='product_id', how='left')
            context['items_mba_completo'] = de_dataframe_a_template(df)
            return context
        else:
            context['items_mba_completo'] = None
            return context


class CartaItemsList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    ''' Lista de cartas generales creadas '''
    model = CartaItem
    queryset = CartaItem.objects.filter(anularcartaitem__isnull=True)
    template_name = 'cartas/carta_items/list_items.html'
    ordering = ['-pk']

    permission_required = 'carta.view_cartaitem'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('items_list'))


@login_required(login_url='login')
def anular_cartaitem(request, slug):
    
    if request.user.has_perm('carta.add_anularcartaitem'):

        carta = CartaItem.objects.get(slug=slug)
        form  = AnularCartaItemForm({
        'cartaitem':carta.pk
        })

        context = {
            'form':form,
            'carta':carta,
        }
        
        if request.method == 'POST':
            form = AnularCartaItemForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('anular_items_list')
    
    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/cartas/items/list')
    
    return render(request, 'cartas/carta_items/anular_cartaitem.html', context)


class AnularCartaItemList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = AnularCartaItem
    template_name = 'cartas/carta_items/list_items_anulada.html'
    permission_required = 'carta.view_anularcartaitem'
    ordering = ['-pk']

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('items_list'))


class CartaItemAnuladaDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = AnularCartaItem
    template_name = 'cartas/carta_items/anular_cartaitems_detail.html'
    permission_required = 'carta.view_anularcartaitem'

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('items_list'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # obtener el valor items_mba de la base de datos del detial
        items_mba_completo = self.object.cartaitem.items_mba
        
        if items_mba_completo:
            items_mba_completo = ast.literal_eval(items_mba_completo)
            df = pd.DataFrame(list(items_mba_completo.items()), columns=['index', 'product_id'])
            df = df.merge(productos_odbc_and_django()[['product_id','Nombre','MarcaDet']], on='product_id', how='left')
            context['items_mba_completo'] = de_dataframe_a_template(df)
            return context
        else:
            context['items_mba_completo'] = None
            return context