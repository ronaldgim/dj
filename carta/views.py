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

    ''' Llenar campos de carga general y crear objeto '''
    form = CartaGeneralForm()
        
    context = {
        'form':form,
    }
    if request.user.has_perm('carta.add_cartageneral'):
        try:
            if request.method == 'GET':
                
                ruc = request.GET['buscar_cliente']
                ruc = str(ruc)
                
                cliente_dict = tabla_clientes(ruc)[0]
                identificacion_fiscal = cliente_dict.get('IDENTIFICACION_FISCAL')
                nombre_cliente = cliente_dict.get('NOMBRE_CLIENTE')
                
                if identificacion_fiscal == '':
                    context = {
                        'error':'El Ruc no coincide con ningun cliente, por favor intente nuevamente!!!'
                    }
                else:
                    context = {
                        'ruc':identificacion_fiscal, 
                        'nombre_cliente':nombre_cliente, 
                        'form':form,
                    }

            elif request.method == 'POST':
                    
                form = CartaGeneralForm(request.POST)
                
                if form.is_valid():
                    form.save()
                    
                    return redirect('general_list')
                
            else:
                context = {'form':form}
        
        except:
            context = {'form':form}

    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('list')

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


# Carta Procesos
@login_required(login_url='login')
def carta_procesos(request):
    ''' Llenar campos de carga general y crear objeto '''
    form = CartaProcesosForm()
    
    context = {
        'form':form,
    }
    
    if request.user.has_perm('carta.add_cartaprocesos'):

        try:
            if request.method == 'GET':
                ruc = request.GET['buscar_cliente']
                ruc = str(ruc)
                
                cliente_dict = tabla_clientes(ruc)[0]
                identificacion_fiscal = cliente_dict.get('IDENTIFICACION_FISCAL')
                nombre_cliente = cliente_dict.get('NOMBRE_CLIENTE')
                if identificacion_fiscal == '':
                    context = {
                        'error':'El Ruc no coincide con ningun cliente, por favor intente nuevamente!!!'
                    }
                else:
                    context = {
                        'ruc':identificacion_fiscal, 
                        'nombre_cliente':nombre_cliente, 
                        'form':form,
                    }

            elif request.method == 'POST':
                    
                form = CartaProcesosForm(request.POST)
                
                if form.is_valid():
                    form.save()
                    return redirect('procesos_list')
            else:
                print(form.errors)
                context = {
                    'form':form,
                    'errors':form.errors                        
                }
        
        except:
            context = {'form':form}
    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('list')
        
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


# Carta Items
@login_required(login_url='login')
def carta_items(request):
    ''' Llenar campos de carga general y crear objeto '''
    form = CartaItemForm()
    
    context = {
        'form':form,
    }
    
    if request.user.has_perm('carta.add_cartaitem'):

        try:
            if request.method == 'GET':
                ruc = request.GET['buscar_cliente']
                ruc = str(ruc)
                
                cliente_dict = tabla_clientes(ruc)[0]
                identificacion_fiscal = cliente_dict.get('IDENTIFICACION_FISCAL')
                nombre_cliente = cliente_dict.get('NOMBRE_CLIENTE')
                if identificacion_fiscal == '':
                    context = {
                        'error':'El Ruc no coincide con ningun cliente, por favor intente nuevamente!!!'
                    }
                else:
                    context = {
                        'ruc':identificacion_fiscal, 
                        'nombre_cliente':nombre_cliente, 
                        'form':form,
                    }

            elif request.method == 'POST':
                    
                form = CartaItemForm(request.POST)
                
                if form.is_valid():
                    form.save()
                    return redirect('items_list')
            else:
                context = {'form':form}
        
        except:
            context = {'form':form}

    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('list')
        
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
