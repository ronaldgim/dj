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
    AnexoDoc
    )

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