# Forms
from django import forms

# Models
from carta.models import CartaGeneral, CartaProcesos, CartaItem, AnularCartaGeneral, AnularCartaProcesos, AnularCartaItem

# MyForms
class CartaGeneralForm(forms.ModelForm):

    class Meta:
        model = CartaGeneral
        fields = '__all__'
        exclude = ['slug', 'qr_code', 'oficio', 'n_ofocio']
        
    
class CartaProcesosForm(forms.ModelForm):
    
    class Meta:
        model = CartaProcesos
        fields = '__all__'
        exclude = ['slug', 'qr_code', 'oficio', 'n_ofocio']


class CartaItemForm(forms.ModelForm):
    
    class Meta:
        model = CartaItem
        fields = '__all__'
        exclude = ['slug', 'qr_code', 'oficio', 'n_ofocio']
        

class AnularCartaGeneralForm(forms.ModelForm):
    
    class Meta:
        model = AnularCartaGeneral
        fields = '__all__'
        exclude = ['slug', 'fecha']


class AnularCartaProcesosForm(forms.ModelForm):
    
    class Meta:
        model = AnularCartaProcesos
        fields = '__all__'
        exclude = ['slug', 'fecha']


class AnularCartaItemForm(forms.ModelForm):
    
    class Meta:
        model = AnularCartaItem
        fields = '__all__'
        exclude = ['slug', 'fecha']