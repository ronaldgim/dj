# Forms 
from django import forms 

# Models
from mantenimiento.models import Equipo, Suministro, Estadistica, Mantenimiento

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