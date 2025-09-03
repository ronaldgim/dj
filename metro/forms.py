from django import forms
from django.contrib.auth.models import User
from metro.models import Product, Inventario, TomaFisica, Kardex


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        exclude = ['usuario', 'unidad', 'u_empaque', 'consignacion']
        labels = {
            'order'       : 'Orden',
            'revisado'    : 'Revisado',
            'codigo_gim'  : 'Código GIM',
            'codigo_hm'   : 'Código HM',
            'nombre_gim'  : 'Nombre GIM',
            'nombre_hm'   : 'Nombre HM',
            'marca'       : 'Marca',
            # 'unidad'      : 'UM',
            # 'u_empaque'   : 'U.Empaque',
            'consignacion': 'Consignación',
            'ubicacion'   : 'Ubicación',
            'activo'      : 'Activo',
            'usuario'     : 'Usuario',
        }
        # help_texts = {
        #     'codigo_gim'  : 'Código GIM',
        #     'codigo_hm'   : 'Código HM',
        #     'u_empaque'   : 'Cantidad de unidades por empaque',
        #     'consignacion': 'Cantidad en consignación (si aplica)',
        #     'ubicacion'   : 'Ubicación física del producto',
        # }
        widgets = {
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Orden'
            }),
            'revisado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'codigo_gim': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. GIM-12345',
                'autocomplete': 'off',
                'data-bs-toggle': 'tooltip',
                'title': 'Ingrese el código GIM único'
            }),
            'codigo_hm': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. HM-12345',
                'autocomplete': 'off'
            }),
            'nombre_gim': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto en GIM'
            }),
            'nombre_hm': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto en HM'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. ANNUY, HSINER, etc'
            }),
            'unidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. UND, CJ, PQ, SB, etc.'
            }),
            'u_empaque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Cantidad por empaque'
            }),
            # 'consignacion': forms.NumberInput(attrs={
            #     'class': 'form-control',
            #     'min': '0',
            #     'placeholder': 'Cantidad en consignación'
            # }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Bodega A, Estante 5, etc.'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Cantidad en consignación'
            }),
            'factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Cantidad en consignación'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
                'id': 'flexSwitchCheckChecked'
            }),
            # 'usuario': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        
        # Marcar campos requeridos para Bootstrap
        for field_name, field in self.fields.items():
            if field.required:
                self.fields[field_name].widget.attrs['required'] = 'required'
                if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.NumberInput):
                    self.fields[field_name].widget.attrs['class'] += ' is-required'
        
        for field_name, field in self.fields.items():
            self.fields[field_name].error_messages = {
                'required': f'{field.label} es requerido.',
                'invalid': f'{field.label} tiene un formato inválido.',
            }
        
    def clean_codigo_gim(self):
        """Validar que el código GIM sea único y tenga el formato correcto"""
        codigo = self.cleaned_data.get('codigo_gim')
        if not self.instance.pk and Product.objects.filter(codigo_gim=codigo).exists():
            raise forms.ValidationError("Este código GIM ya existe en el sistema.")
        
        # Aquí podrías agregar validación personalizada del formato
        return codigo
        
    def clean_u_empaque(self):
        """Asegurar que unidades por empaque sea un número positivo"""
        u_empaque = self.cleaned_data.get('u_empaque')
        if u_empaque is not None and u_empaque < 0:
            raise forms.ValidationError("Las unidades por empaque no pueden ser negativas.")
        return u_empaque


class InventarioForm(forms.ModelForm):

    class Meta:
        model = Inventario
        fields = '__all__'
        exclude = ['usuario', 'estado_inv', 'estado_tf', 'inicio_tf', 'fin_tf']
        labels = {
            'nombre' : 'Nombre',
        }

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inventario 001',
                'autocomplete': 'off',
                'data-bs-toggle': 'tooltip',
                'title': 'Nombre de inventario'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(InventarioForm, self).__init__(*args, **kwargs)
        
        # Marcar campos requeridos para Bootstrap
        for field_name, field in self.fields.items():
            if field.required:
                self.fields[field_name].widget.attrs['required'] = 'required'
                if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.NumberInput):
                    self.fields[field_name].widget.attrs['class'] += ' is-required'
        
        for field_name, field in self.fields.items():
            self.fields[field_name].error_messages = {
                'required': f'{field.label} es requerido.',
                'invalid': f'{field.label} tiene un formato inválido.',
            }


class TomaFisicaForm(forms.ModelForm):
    class Meta:
        model = TomaFisica
        fields = '__all__'
        exclude = ['usuario', 'product', 'inventario', 'llenado', 'agregado', 'cantidad_total']
        labels = {
            # 'cantidad_estanteria'  : 'Und. Estanteria (+, -)',
            'cantidad_estanteria'  : 'Bodega General (+, -)',
            
            # 'cantidad_bulto'  : 'Und. Bulto (+, -)',
            'cantidad_bulto'  : 'Otras Bodegas (+, -)',
            
            # 'cantidad_suministro'  : 'Und. Suministro (+, -)',
            'cantidad_suministro'  : 'Bodega Suministro (+, -)',
            
            'observaciones':'Observaciones',
        }
        # help_texts = {
        #     'codigo_gim'  : 'Código GIM',
        #     'codigo_hm'   : 'Código HM',
        #     'u_empaque'   : 'Cantidad de unidades por empaque',
        #     'consignacion': 'Cantidad en consignación (si aplica)',
        #     'ubicacion'   : 'Ubicación física del producto',
        # }
        widgets = {
            
            # 'cantidad_estanteria': forms.NumberInput(attrs={
            'cantidad_estanteria': forms.TextInput(attrs={  
                'class': 'form-control',
                # 'min': '0',
                'placeholder': 'Und.Estanteria',
                'inputmode':'numeric',
                #'pattern':'^\+?\d*$'
            }),
            
            # 'cantidad_bulto': forms.NumberInput(attrs={
            'cantidad_bulto': forms.TextInput(attrs={
                'class': 'form-control',
                # 'min': '0',
                'placeholder': 'Uni.Bulto',
                'inputmode':'numeric',
            }),
            
            # 'cantidad_suministro': forms.NumberInput(attrs={
            'cantidad_suministro': forms.TextInput(attrs={
                'class': 'form-control',
                # 'min': '0',
                'placeholder': 'Und.Suministro',
                'inputmode':'numeric',
            }),
            
            # 'observaciones': forms.TextInput(attrs={
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '',
                'autocomplete': 'off',
                'cols': '1',
                'rows':'2'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TomaFisicaForm, self).__init__(*args, **kwargs)
        
        # Marcar campos requeridos para Bootstrap
        for field_name, field in self.fields.items():
            if field.required:
                self.fields[field_name].widget.attrs['required'] = 'required'
                if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.NumberInput):
                    self.fields[field_name].widget.attrs['class'] += ' is-required'
        
        for field_name, field in self.fields.items():
            self.fields[field_name].error_messages = {
                'required': f'{field.label} es requerido.',
                'invalid': f'{field.label} tiene un formato inválido.',
            }
        
        
    def clean_cantidad_estanteria(self):
        """Asegurar que cantidad_estanteria sea un número positivo"""
        cantidad_estanteria = self.cleaned_data.get('cantidad_estanteria')
        if cantidad_estanteria is not None and cantidad_estanteria < 0:
            raise forms.ValidationError("Las unidades en estanteria no pueden ser negativas.")
        return cantidad_estanteria
    
    def clean_cantidad_bulto(self):
        """Asegurar que cantidad_bulto sea un número positivo"""
        cantidad_bulto = self.cleaned_data.get('cantidad_bulto')
        if cantidad_bulto is not None and cantidad_bulto < 0:
            raise forms.ValidationError("Las unidades en bulto no pueden ser negativas.")
        return cantidad_bulto
    
    def clean_cantidad_suministro(self):
        """Asegurar que cantidad_suministro sea un número positivo"""
        cantidad_suministro = self.cleaned_data.get('cantidad_suministro')
        if cantidad_suministro is not None and cantidad_suministro < 0:
            raise forms.ValidationError("Las unidades en suministro no pueden ser negativas.")
        return cantidad_suministro


class KardexForm(forms.ModelForm):
    class Meta:
        model = Kardex
        fields = '__all__'
        exclude = ['creado', 'actualizado'] #,'confirmado']
        labels = {
            # 'tipo': 'Tipo de Movimiento',
            'description': 'Descripción del Movimiento',
            'nota_entrega': 'Nota de Entrega',
            'fecha_nota': 'Fecha Nota de Entrega',
            'movimiento_mba': 'Movimiento MBA',
            'fecha_mba': 'Fecha Movimiento MBA',
            'cantidad': 'Cantidad (+ / -)',
            'documento': 'Documento adjunto',
            'observaciones': 'Observaciones',
        }
        widgets = {
            # 'tipo': forms.Select(attrs={
            #     'class': 'form-select',
            # }),
            'description': forms.Select(attrs={
                'class': 'form-select',
            }),
            'nota_entrega': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de nota de entrega',
            }),
            'fecha_nota': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            },
                format='%Y-%m-%d'
            ),
            'movimiento_mba': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Movimiento MBA',
            }),
            'fecha_mba': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            },
                format='%Y-%m-%d'
            ),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'inputmode': 'numeric',
            }),
            'documento': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones adicionales',
            }),
            'usuario': forms.HiddenInput(),
            'product': forms.HiddenInput(),
            
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(KardexForm, self).__init__(*args, **kwargs)

        # Marcar campos requeridos para Bootstrap
        for field_name, field in self.fields.items():
            if field.required:
                self.fields[field_name].widget.attrs['required'] = 'required'
                if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                    self.fields[field_name].widget.attrs['class'] += ' is-required'

        # Mensajes de error personalizados
        for field_name, field in self.fields.items():
            self.fields[field_name].error_messages = {
                'required': f'{field.label} es requerido.',
                'invalid': f'{field.label} tiene un formato inválido.',
            }

    def clean_cantidad(self):
        """Asegurar que la cantidad no sea cero"""
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad == 0:
            raise forms.ValidationError("La cantidad no puede ser cero.")
        return cantidad

