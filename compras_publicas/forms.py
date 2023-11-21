# Forms 
from django import forms 

# Models
from compras_publicas.models import ProcesosSercop

# MyForms

# Equipo Form

class ProcesosSercopForm(forms.ModelForm):
    
    class Meta:
        model = ProcesosSercop
        fields = '__all__'