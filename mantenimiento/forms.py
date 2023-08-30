# Forms 
from django import forms 

# Models
from mantenimiento.models import Equipo, Suministro, Estadistica, Mantenimiento, MantenimientoPreventivo

# MyForms

# Equipo Form
class EquipoCreateForm(forms.ModelForm):
    
    class Meta:
        model = Equipo
        fields = '__all__'
        exclude = ['slug']


# Suministro Form
class SuministroForm(forms.ModelForm):
    
    class Meta:
        model = Suministro
        fields = '__all__'
        exclude = ['slug']


# Estadistica Form
class EstadisticaForm(forms.ModelForm):
    
    class Meta:
        model = Estadistica
        fields = '__all__'
        exclude = ['slug']


# Mantenimiento Form
class MantenimientoForm(forms.ModelForm):
    
    class Meta:
        model = Mantenimiento
        fields = '__all__'
        exclude = ['slug']
        
        
### MANTENIMIENTOS PREVENTIVOS        
# Crear Mantenimiento 
class MantenimientoPreventivoCrearForm(forms.ModelForm):
    
    class Meta:
        model = MantenimientoPreventivo
        fields = [
            'equipo',
            'responsable',
            'estado',
            'programado',
            'actividad'
        ]
        
# Realizar Mantenimiento 
class MantenimientoPreventivoRealizarForm(forms.ModelForm):
    
    class Meta:
        model = MantenimientoPreventivo
        fields = [
            'user',
            'realizado',
            'estado',
            'observaciones',
            'foto'
        ]