# Forms 
from django import forms 

# Models
from wms.models import Movimiento

# MyForms

# Equipo Form

class MovimientosForm(forms.ModelForm):
    
    class Meta:
        model = Movimiento
        fields = '__all__'
        