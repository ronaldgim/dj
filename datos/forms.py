# Forms
from django import forms

# Models
from datos.models import Product #, MarcaImportExcel, 

# Forms

# class MarcaImportExcelForm(forms.ModelForm):
    
#     class Meta:
#         model = MarcaImportExcel
#         fields = '__all__'


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'