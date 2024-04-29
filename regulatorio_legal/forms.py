# Forms 
from django import forms 

# Models
from regulatorio_legal.models import DocumentoLote, DocumentoEnviado

# MyForms

# Equipo Form

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