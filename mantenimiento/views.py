# DB
from django.db import connections
import pandas as pd

# Models
from mantenimiento.models import Equipo, Suministro, Estadistica, Mantenimiento, MantenimientoPreventivo

# Generic Views
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

# Forms
from mantenimiento.forms import (
    EquipoCreateForm, 
    SuministroForm, 
    EstadisticaForm, 
    MantenimientoForm,
    MantenimientoPreventivoCrearForm,
    MantenimientoPreventivoRealizarForm)

# Urls
from django.urls import reverse

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

#Json
import json

# Shorcuts
from django.shortcuts import render, redirect

# importar datos de excel
# def impor_data(request):
    
#     # transformar excel
#     #data = pd.read_excel('C:\Erik\Egares Gimpromed\Desktop/estadisticas.xlsx')
#     data = pd.read_excel('C:\Erik\Egares Gimpromed\Desktop/data_etiquetadoras/estadisticas_me.xlsx')
#     data = data.to_dict('records')
            
#     data_import = []
#     pk = 0
            
#     for i in data:
#         #pk  = i.get('id')
#         pk += 1
#         p_d = i.get('p_detectados')
#         c_m = i.get('c_mens')
#         f_s = i.get('f_seniales')
#         h_m = i.get('h_m_ms')
#         h_c = i.get('h_c_ms')
#         obs = i.get('observacion')
#         fec = i.get('Fecha ')
#         slg = i.get('slug')
#         eid = i.get('equipo_id')
        
#         est = (pk, p_d, c_m, f_s, h_m, h_c, obs, fec, slg, eid)
#         data_import.append(est)        
    
#     if request.method == 'GET':
        
#         print(data_import)
#         with connections['default'].cursor() as cursor:
#             cursor.executemany(
#                 "INSERT INTO mantenimiento_estadistica (id, p_detectados, c_mens, f_seniales, h_maquina, h_chorro, observacion, fecha, slug, equipo_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data_import
#                 #"REPLACE INTO mantenimiento_estadistica (id, p_detectados, c_mens, f_seniales, h_maquina, h_chorro, observacion, fecha, slug, equipo_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data_import
#             )



# EQUIPOS VIEWS
# Lista de equipos
class EquipoList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = Equipo
    template_name = 'mantenimiento/equipo/list.html'

    permission_required = 'carta.view_equipo'
 
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        messages.error(self.request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect(reverse_lazy('inicio'))


# Crear equipo
class EquipoCreate(CreateView):
    model = Equipo
    form_class = EquipoCreateForm
    success_url = 'list'
    template_name = 'mantenimiento/equipo/new.html'


# SUMINISTRO
# Lista de insumos o repuestos
class SuministroList(ListView):
    model = Suministro
    template_name = 'mantenimiento/suministro/list.html'
    

# Crear suministro
class SuministroCreate(CreateView):
    model = Suministro
    form_class = SuministroForm
    success_url = 'list'
    template_name = 'mantenimiento/suministro/new.html'


# ESTADISTICA
# Lista de estadisticas
# A200+
class EstadisticaList(ListView):
    model = Estadistica
    queryset = Estadistica.objects.filter(equipo=1)
    ordering = ['-fecha']
    template_name = 'mantenimiento/estadistica/list.html'

    def get_context_data(self, *args,**kwargs):
        context = super(EstadisticaList, self).get_context_data(*args,**kwargs)
        data = pd.DataFrame(Estadistica.objects.filter(equipo=1).values())

        indice = []
        for i in range(len(data)):
            indice.append(i)

        data = data[['p_detectados', 'h_maquina']]
        data['ind'] = indice

        par = []
        inpar = []
        # for i in range(len(data)):
        #     if i & 1 == 0:
        #         print(i)

        for i in data.iterrows():
            if i[0] & 1 == 0:
                p = i[1][0]
                par.append(p)
            else:
                inp = i[1][0]
                inpar.append(inp)
            #if i & 1 == 0:
            #print(i[0] ,i[1][0] ,i[1][1])

        p_eti = pd.DataFrame(list(zip(par, inpar)), columns=['par', 'inpar'])
        p_eti['p_eti'] = p_eti['inpar'] - p_eti['par']
        #print(p_eti)

        #print(data)

        return context
    

def diferencia_columna(lista):
    lista_dif = []
    primero = lista[0]
    for i in range(len(lista)-1):
        i += 1
        j = i + 2
        x = i - 1
        y = j - 1
        
        p = lista[x:y][1] - lista[x:y][0]
        lista_dif.append(p)
        
    lista_dif.insert(0, primero)
    
    return lista_dif


def lista_estadisticas(request, equipo):

    eq = Equipo.objects.get(id=equipo)
    eq = eq.nombre
    print(eq)
    est = pd.DataFrame(Estadistica.objects.filter(equipo_id=equipo).values())
    p_d = list(est['p_detectados'])
    h_m = list(est['h_maquina'])
    h_c = list(est['h_chorro'])

    est['productos_etiquetados'] = diferencia_columna(p_d)
    est['horas_encendido'] = diferencia_columna(h_m)
    est['horas_trabajo'] = diferencia_columna(h_c)

    est['fecha'] = est['fecha'].astype(str)

    est = est[[
        'fecha',
        'p_detectados',
        'c_mens',
        'f_seniales',
        'h_maquina',
        'h_chorro',
        'productos_etiquetados',
        'horas_encendido',
        'horas_trabajo',
        'observacion'
    ]]
    
    json_records = est.reset_index().to_json(orient='records') # reset_index().
    est = json.loads(json_records)
    
    context = {
        'object_list':est,
        'equipo':eq
    }
    
    return render(request, 'mantenimiento/estadistica/list2.html', context)



# Crear equipo
class EstadisticaCreate(CreateView):
    model = Estadistica
    form_class = EstadisticaForm
    success_url = 'list'
    template_name = 'mantenimiento/estadistica/new.html'


# MANTENIMIENTO
# Lista de mantenimiento
class MantenimientoList(ListView):
    model = Mantenimiento
    template_name = 'mantenimiento/mantenimiento/list.html'
    

# Crear un mantenimiento
class MantenimientoCreate(CreateView):
    model = Mantenimiento
    form_class = MantenimientoForm
    success_url = 'list'
    template_name = 'mantenimiento/mantenimiento/new.html'
    
    
    
### MANTENIMIENTOS PREVENTIVOS
# Lista de mantenimientos
def list_mpreventivos(request):
    
    m_preventivos = MantenimientoPreventivo.objects.all().order_by('-programado')
    
    context = {
        'm_preventivos':m_preventivos
    }
    
    return render(request, 'mantenimiento/mtto_preventivo/list.html', context)


# Lista de mantenimientos
def list_mpreventivos_por_realizar(request):
    from datetime import datetime
    
    month = datetime.now().month + 1
    year  = datetime.now().year
    
    m_preventivos = (MantenimientoPreventivo.objects
                        .filter(estado='PENDIENTE')
                        .filter(programado__month = month)
                        .filter(programado__year  = year)
                        .order_by('-programado')
                    )
    
    context = {
        'm_preventivos':m_preventivos
    }
    
    return render(request, 'mantenimiento/mtto_preventivo/list_pendientes.html', context)


# Crear mantenimiento preventivo
# def nuevo_mpreventivo(request):
    
#     form = MantenimientoPreventivoCrearForm()
    
#     if request.method == 'POST':
#         form = MantenimientoPreventivoCrearForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Mantenimiento preventivo creado correctamente')
#             return redirect('preventivo_list')
        
#         else:
#             messages.error(request, 'Error al crear mantenimiento preventivo')
            
#     context = {
#         'form':form
#     }
    
#     return render(request, 'mantenimiento/estadistica/list2.html', context)


# Realizar mantenimiento preventivo
def realizar_mpreventivo(request, id):
    
    form = MantenimientoPreventivoRealizarForm()
    inst = MantenimientoPreventivo.objects.get(id=id)
    
    if request.method == 'POST':
        form = MantenimientoPreventivoRealizarForm(request.POST, request.FILES, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mantenimiento preventivo realizado correctamente')
            return redirect('preventivo_list')
        
        else:
            messages.error(request, 'Error al realizar mantenimiento preventivo')
            
    context = {
        'inst':inst,
        'form':form
    }
    
    return render(request, 'mantenimiento/mtto_preventivo/realizar.html', context)

