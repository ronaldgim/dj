# Forms 
from django import forms 

# Models
from wms.models import Movimiento, Ubicacion

# MyForms

# Equipo Form

class MovimientosForm(forms.ModelForm):
    
    class Meta:
        model = Movimiento
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ubicacion'].queryset = Ubicacion.objects.filter(disponible=True)
        