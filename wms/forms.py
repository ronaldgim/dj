# Forms 
from django import forms 

# Models
from wms.models import (
    Movimiento, 
    Ubicacion, 
    DespachoCarton,
    ProductoArmado,
    OrdenEmpaque
    )

# MyForms

# Equipo Form

class MovimientosForm(forms.ModelForm):
    
    class Meta:
        model = Movimiento
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ubicacion'].queryset = Ubicacion.objects.filter(disponible=True)


class DespachoCartonForm(forms.ModelForm):
    
    class Meta:
        model = DespachoCarton
        fields = '__all__'
        

class ProductoArmadoForm(forms.ModelForm):
    
    class Meta:
        model = ProductoArmado
        fields = '__all__'
        

class OrdenEmpaqueForm(forms.ModelForm):
    
    class Meta:
        model = OrdenEmpaque
        fields = [
            'ruc',
            'cliente',
            'bodega',
            'prioridad',
            'estado',
            'usuario',
            'observaciones'
        ]
        
        widgets = {
            'ruc':forms.TextInput(attrs={'class':'form-control','list':'ruc_list'}),
            'cliente':forms.TextInput(attrs={'class':'form-control', 'list':'cliente_list'}),
            'bodega':forms.Select(attrs={'class':'form-select'}),
            'prioridad':forms.Select(attrs={'class':'form-select'}),
            'observaciones':forms.Textarea(attrs={'class':'form-control', 'rows':'2'}),
            'estado':forms.TextInput(attrs={'type':'hidden'}),
            'usuario':forms.TextInput(attrs={'type':'hidden'}),
        }