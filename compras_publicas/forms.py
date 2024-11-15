# Forms 
from django import forms 

# Models
from compras_publicas.models import ProcesosSercop, Producto

# MyForms

# Equipo Form

class ProcesosSercopForm(forms.ModelForm):
    
    class Meta:
        model = ProcesosSercop
        fields = ['proceso']
        
        
class ProcesosSercopFormUpdate(forms.ModelForm):
    
    class Meta:
        model = ProcesosSercop
        fields = '__all__'
        
class ProductoForm(forms.ModelForm):
    
    class Meta:
        model = Producto
        fields = '__all__'
        # fields = [
        #     'product_id',
        #     'nombre',
        #     'nombre_generico',
        #     'presentacion',
        #     'marca',
        #     'procedencia',
        #     'r_sanitario',
        #     'lote_id',
        #     'f_elaboracion',
        #     'f_caducidad',
        #     'cantidad',
        #     ]