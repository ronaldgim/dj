# Forms 
from django import forms 

# Models
from inventario.models import Inventario, InventarioTotale, Arqueo
from users.models import User

# MyForms
# Inventario actualizar toma física 
class InventarioForm(forms.ModelForm):

    class Meta:
        model = Inventario
        fields = [
        'unidades_caja', 
        'numero_cajas', 
        'unidades_sueltas', 
        'observaciones',
        'llenado',
        'user'
        ]


# Inventario Agregar
class InventarioAgregarForm(forms.ModelForm):

    class Meta:
        model = Inventario
        fields = '__all__'


# Inventarios Totales
class InventarioTotalesForm(forms.ModelForm):

    class Meta:
        model = InventarioTotale
        fields = '__all__'
        

# Arqueo
class ArqueoForm(forms.ModelForm):

    class Meta:
        model = Arqueo
        fields = '__all__'
