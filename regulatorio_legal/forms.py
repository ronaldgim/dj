# date
import datetime 
# Forms 
from django import forms 

# Models
from regulatorio_legal.models import (
    DocumentoLote, 
    DocumentoEnviado, 
    DocumentosLegales, 
    RegistroSanitario,
    DocumentoVario,
    Documento
    )
    



# MyForms
class DocumentoLoteForm(forms.ModelForm):
    
    class Meta:
        model = DocumentoLote
        fields = ['documento']


class NewDocumentoLoteForm(forms.ModelForm):
    
    class Meta:
        model = DocumentoLote
        fields = '__all__'


class DocumentoEnviadoForm(forms.ModelForm):
    
    class Meta:
        model = DocumentoEnviado
        fields = '__all__'
        

class DocumentosLegalesForm(forms.ModelForm):
    
    class Meta:
        model = DocumentosLegales
        
        fields = [
            'marca',
            'nombre_proveedor',
            'documento',
            'fecha_caducidad',
            'usuario'
        ]

        labels = {
            'marca': 'Marca',
            'nombre_proveedor': 'Proveedor',
            'documento': 'Documento',
            'fecha_caducidad': 'Fecha de Caducidad',
        }

        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept':'application/pdf,application'}),
            'fecha_caducidad': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control','type': 'date'}),
            'usuario':forms.TextInput(attrs={'type':'hidden'})
        }

class RegistroSanitarioForm(forms.ModelForm):
    
    class Meta:
        model = RegistroSanitario
        
        fields = [
            'n_reg_sanitario',
            'descripcion',
            'fecha_caducidad',
            'documento',
            'usuario',
        ]
        
        labels = {
            'n_reg_sanitario': 'N° Registro Sanitario',
            'descripcion': 'Descripción',
            'fecha_caducidad': 'Fecha de Caducidad',
            'documento': 'Documento',
        }
        
        widgets = {
            'n_reg_sanitario': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept':'application/pdf,application'}),
            'fecha_caducidad': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control','type': 'date'}),
            'usuario':forms.TextInput(attrs={'type':'hidden'}),
        }


class DocumentoVarioForm(forms.ModelForm):
    
    class Meta:
        model = DocumentoVario
        fields = '__all__'

        
class DocumentoForm(forms.ModelForm):
    
    class Meta:
        model = Documento
        fields = '__all__'