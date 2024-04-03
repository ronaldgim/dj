# Forms
from django import forms

# Models
from bpa.models import RegistroSanitario, CartaNoRegistro

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
