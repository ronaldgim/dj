# Models
from django.db import models

# Usuario
from users.models import User



# Selects
TIPOS_MOVIMIENTOS = [
    ('Ingreso', 'Ingreso'),
    ('Egreso', 'Egreso'),
]

REFERENCIA_MOVIMIENTOS = [
    ('Inventario Inicial', 'Inventario Inicial'),
    ('Ingreso Importación', 'Ingreso Importación'),
    ('Movimiento Interno',  'Movimiento Interno'),
    ('Liberación', 'Liberación'),
    ('Ajuste', 'Ajuste'),
    ('Picking', 'Picking'),
]

REFERENCIA_INGRESOS = [
    ('Inventario Inicial', 'Inventario Inicial'),
    ('Ingreso Importación', 'Ingreso Importación'),
    ('Liberación', 'Liberación'),
    ('Ajuste', 'Ajuste'),
]

BODEGA = [
    ('CN4', 'CN4'),
    ('CN5', 'CN5'),
    ('CN6', 'CN6'),
    ('CN7', 'CN7'),
    ('CUC', 'CUC'),
]

PASILLO = [
    ('A', 'A'),
    ('B', 'B'),
]

MODULO = [
    ('01', '01'),
    ('02', '02'),
    ('03', '03'),
    ('04', '04'),
    ('05', '05'),
    ('06', '06'),
    ('07', '07'),
    ('08', '08'),
    ('09', '09'),
]

NIVEL = [
    ('01', '01'),
    ('02', '02'),
    ('03', '03'),
    ('04', '04'),
    ('05', '05'),
    ('06', '06'),
]


# Create your models here.
class InventarioIngresoBodega(models.Model):
    
    product_id          = models.CharField(verbose_name='Product id', max_length=50)
    lote_id             = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad     = models.DateField(verbose_name='Fecha de caducidad')
    bodega              = models.CharField(verbose_name='Bodega', choices=BODEGA, max_length=5)
    unidades_ingresadas = models.IntegerField(verbose_name='Unidades ingresadas')
    referencia          = models.CharField(verbose_name='Referencia', choices=REFERENCIA_INGRESOS, max_length=50) 
    n_referencia        = models.CharField(verbose_name='N°. Referencia', max_length=50, blank=True)
    id_ref              = models.IntegerField(verbose_name='Id referencia', blank=True, default=0)
    fecha_hora          = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)

    def __str__(self):
        return f"código:{self.product_id} - unidades: {self.unidades_ingresadas}" 
    


class Ubicacion(models.Model):

    bodega       = models.CharField(verbose_name='Bodega', choices=BODEGA, max_length=10)
    pasillo      = models.CharField(verbose_name='Pasillo', choices=PASILLO, max_length=10)
    modulo       = models.CharField(verbose_name='Modulo', choices=MODULO, max_length=10)
    nivel        = models.CharField(verbose_name='Nivel', choices=NIVEL, max_length=10)
    capacidad_m3 = models.FloatField(verbose_name='Capacidad m3')
    distancia_puerta = models.FloatField(verbose_name='Capacidad m3', blank=True, null=True)
    

    def __str__(self):
        return f"{self.bodega}.{self.pasillo}.{self.modulo}.{self.nivel}"
        # return f"{self.pasillo}.{self.modulo}.{self.nivel}"



class Movimiento(models.Model):

    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
    tipo            = models.CharField(verbose_name='Tipo de movimiento', choices=TIPOS_MOVIMIENTOS, max_length=10)
    descripcion     = models.CharField(verbose_name='Descripción del movimiento', max_length=20, blank=True)
    referencia      = models.CharField(verbose_name='Referencia del movimiento', choices=REFERENCIA_MOVIMIENTOS, max_length=20, blank=True)
    n_referencia    = models.CharField(verbose_name='Numero de referencia',max_length=20, blank=True)
    ubicacion       = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='ubicacion')
    unidades        = models.IntegerField(verbose_name='Unidades ingresadas')
    cuarentena      = models.BooleanField(verbose_name='Cuarentena', default=True)
    despacho        = models.BooleanField(verbose_name='Despacho', default=False)

    usuario         = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.CASCADE, blank=True, null=True)
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)

    def __str__(self):
        #return str(self.tipo, self.product_id)
        return self.product_id


class Existencias(models.Model):
    
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
    ubicacion       = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='existencias_ubicacion')
    unidades        = models.PositiveIntegerField(verbose_name='Unidades ingresadas')
    cuarentena      = models.BooleanField(verbose_name='Cuarentena', default=False)
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    
    def __str__(self):
        return self.product_id
    
    
# class Liberacion(models.Model):
    
#     documento  = models.CharField(verbose_name='Documento', max_length=100, unique=True)
#     memo       = models.TextField(verbose_name='Memo', blank=True)
#     fecha_mba  = models.DateField(verbose_name='Fecha MBA', blank=True)
    
#     product_id = models.CharField(verbose_name='Product id', max_length=50)
#     lote_id    = models.CharField(verbose_name='Lote id', max_length=50)
#     fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
#     unidades        = models.PositiveIntegerField(verbose_name='Unidades ingresadas')
    
#     usuario    = models.ForeignKey(User, verbose_name='User', blank=True, on_delete=models.CASCADE)
#     fecha_hora = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    
#     def __str__(self):
#         return self.documento
    