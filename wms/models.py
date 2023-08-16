# Models
from django.db import models

# Usuario
from users.models import User


# Selects
TIPOS_MOVIMIENTOS = [
    ('Ingreso', 'Ingreso'),
    ('Egreso', 'Egreso'),
]

DESCRIPCION_MOVIMIENTOS = [
    ('Ingreso Importación', 'Ingreso Importación'),
    ('Movimiento Interno', 'Movimiento Interno'),
    ('Egreso Picking',     'Egreso Picking'),
    ('Ajuste Inventario',  'Ajuste Inventario'),
]

REFERENCIA_MOVIMIENTOS = [
    ('Picking', 'Picking'),
    ('Ajuste', 'Ajuste'),
]


BODEGA = [
    ('CN4', 'CN4'),
    ('CN5', 'CN5'),
    ('CN6', 'CN6'),
    ('CN7', 'CN7'),
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
    
    o_compra            = models.CharField(verbose_name='Orden de compra', max_length=50)
    product_id          = models.CharField(verbose_name='Product id', max_length=50)
    nombre              = models.CharField(verbose_name='Nombre', max_length=50, blank=True)
    marca               = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    marca2              = models.CharField(verbose_name='Marca 2', max_length=50, blank=True)
    lote_id             = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad     = models.DateField(verbose_name='Fecha de caducidad')
    bodega              = models.CharField(verbose_name='Bodega', max_length=5)
    unidades_ingresadas = models.IntegerField(verbose_name='Unidades ingresadas')

    def __str__(self):
        return f"código:{self.product_id} - unidades: {self.unidades_ingresadas}" 
    


class Ubicacion(models.Model):

    bodega       = models.CharField(verbose_name='Bodega', choices=BODEGA, max_length=10)
    pasillo      = models.CharField(verbose_name='Pasillo', choices=PASILLO, max_length=10)
    modulo       = models.CharField(verbose_name='Modulo', choices=MODULO, max_length=10)
    nivel        = models.CharField(verbose_name='Nivel', choices=NIVEL, max_length=10)
    capacidad_m3 = models.FloatField(verbose_name='Capacidad m3')

    def __str__(self):
        return f"{self.bodega}.{self.pasillo}.{self.modulo}.{self.nivel}"
        # return f"{self.pasillo}.{self.modulo}.{self.nivel}"
        


class Movimiento(models.Model):

    item         = models.ForeignKey(InventarioIngresoBodega, verbose_name='Item', on_delete=models.CASCADE, related_name='item')
    tipo         = models.CharField(verbose_name='Tipo de movimiento', choices=TIPOS_MOVIMIENTOS, max_length=10)
    descripcion  = models.CharField(verbose_name='Descripción del movimiento', choices=DESCRIPCION_MOVIMIENTOS, max_length=20, blank=True)
    referencia   = models.CharField(verbose_name='Referencia del movimiento', choices=REFERENCIA_MOVIMIENTOS, max_length=20, blank=True)
    n_referencia = models.CharField(verbose_name='Numero de referencia',max_length=20, blank=True)
    ubicacion    = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='ubicacion')
    unidades     = models.IntegerField(verbose_name='Unidades ingresadas')

    usuario = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.CASCADE, blank=True, null=True)
    fecha_hora = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)

    def __str__(self):
        return str(self.item)
