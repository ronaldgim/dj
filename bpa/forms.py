# Forms
from django import forms

# Models
from bpa.models import RegistroSanitario, CartaNoRegistro, ImportacionesExcel

# My forms
# Reg Sanitario Form
class RegistroSanitarioForm(forms.ModelForm):
    class Meta:
        model = RegistroSanitario
        fields = '__all__'
    

# Reg Sanitario Form
class CartaNoRegistroForm(forms.ModelForm):
    class Meta:
        model = CartaNoRegistro
        fields = '__all__'


# Importación Excel
class ImportacionExcelForm(forms.ModelForm):
    class Meta:
        model = ImportacionesExcel
        fields = '__all__'