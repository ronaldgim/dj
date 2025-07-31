# Forms 
from django import forms 

# Models
from etiquetado.models import (
    Calculadora, 
    RowItem, 
    PedidosEstadoEtiquetado, 
    EstadoPicking, 
    RegistoGuia, 
    FechaEntrega, 
    InstructivoEtiquetado,
    AnexoGuia,
    AnexoDoc,
    UbicacionAndagoya,
    ProductoUbicacion,
    PedidoTemporal,
    ProductosPedidoTemporal,
    # TransfCerAnd
    )

from datos.models import Vehiculos

# MyForms
# Equipo Form

class AnexoGuiaForm(forms.ModelForm):
    
    class Meta:
        model = AnexoGuia
        fields = [
                'bodega_nombre',
                #'estado',
            ]
        
        
class AnexoDocForm(forms.ModelForm):
    class Meta:
        model = AnexoDoc
        fields = '__all__'


class RowItemForm(forms.ModelForm):
    
    class Meta:
        model = RowItem
        fields = '__all__'


class CalculadoraForm(forms.ModelForm):
    
    class Meta:
        model = Calculadora
        fields = '__all__'


class PedidosEstadoEtiquetadoForm(forms.ModelForm):
    
    class Meta:
        model = PedidosEstadoEtiquetado
        fields = '__all__'


class EstadoPickingForm(forms.ModelForm):
    
    class Meta:
        model = EstadoPicking
        fields = '__all__'


class RegistroGuiaForm(forms.ModelForm):
    
    class Meta:
        model = RegistoGuia
        fields = '__all__'


class FechaEntregaForm(forms.ModelForm):
    
    class Meta:
        model = FechaEntrega
        fields = '__all__'
        
        
## Instructivo etiquetado
class InstructivoEtiquetadoForm(forms.ModelForm):
    
    class Meta:
        model = InstructivoEtiquetado
        fields = '__all__'


class UbicacionAndagoyaForm(forms.ModelForm):
    
    class Meta:
        model = UbicacionAndagoya
        fields = ['bodega','pasillo','estanteria','modulo','nivel']
        labels = {
            'bodega'    : 'Edificio-Piso',
            'pasillo'   : 'Sección-Fila',
            'estanteria': 'Estanteria',
            'modulo'    : 'Estanteria',
            'nivel'     : 'Bandeja',
        }
        widgets = {
            'bodega': forms.Select(attrs={'class': 'form-select'}),
            'pasillo': forms.Select(attrs={'class': 'form-select'}),
            'estanteria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'modulo': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProductoUbicacionForm(forms.ModelForm):
    
    class Meta:
        model = ProductoUbicacion
        fields = '__all__'

class PedidoTemporalForm(forms.ModelForm):
    
    class Meta:
        model = PedidoTemporal
        # fields = '__all__'
        exclude = ('productos',)


class ProductosPedidoTemporalForm(forms.ModelForm):
    
    class Meta:
        model = ProductosPedidoTemporal
        fields = '__all__'


# class TransfCerAndForm(forms.ModelForm):
    
#     class Meta:
#         model = TransfCerAnd
#         fields = ['nombre','vehiculo']
#         widgets = {
#             'nombre': forms.TextInput(attrs={'class': 'form-control'}),
#             'vehiculo': forms.Select(attrs={'class': 'form-select'}),
#         }
#     def __init__(self, *args, **kwargs):        
#         super().__init__(*args, **kwargs)
#         self.fields['vehiculo'].queryset = Vehiculos.objects.filter(transportista='GIMPROMED')