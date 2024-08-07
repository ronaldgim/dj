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
    ('Reverso de picking', 'Reverso de picking'),
    ('Transferencia', 'Transferencia'),
    ('Nota de entrega', 'Nota de entrega'),
]

REFERENCIA_INGRESOS = [
    ('Inventario Inicial', 'Inventario Inicial'),
    ('Ingreso Importación', 'Ingreso Importación'),
    ('Liberación', 'Liberación'),
    ('Ajuste', 'Ajuste'),
]

ESTADO = [
    ('Cuarentena', 'Cuarentena'),
    ('Disponible', 'Disponible'),
]

ESTADO_PICKING = [
    ('En Despacho', 'En Despacho'),
    ('Despachado', 'Despachado'),
    ('No Despachado', 'No Despachado'),
]

BODEGA = [
    ('CN4', 'CN4'),
    ('CN5', 'CN5'),
    ('CN6', 'CN6'),
    ('CN7', 'CN7'),
]

TIPO_LIBERACION = [
    ('Liberación Acondicionamiento', 'Liberación Acondicionamiento'),
    ('Liberación Importación', 'Liberación Importación'),
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
    id_ref              = models.IntegerField(verbose_name='Id referencia', blank=True, null=True)
    fecha_hora          = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)

    def __str__(self):
        return f"código:{self.product_id} - unidades: {self.unidades_ingresadas}" 
    


class Ubicacion(models.Model):

    bodega           = models.CharField(verbose_name='Bodega', choices=BODEGA, max_length=10)
    pasillo          = models.CharField(verbose_name='Pasillo', max_length=10)
    modulo           = models.CharField(verbose_name='ModuloPalet', max_length=10)
    nivel            = models.CharField(verbose_name='Nivel', max_length=10)
    capacidad_m3     = models.FloatField(verbose_name='Capacidad m3')
    distancia_puerta = models.FloatField(verbose_name='Distancia a puerta', blank=True, null=True)
    disponible       = models.BooleanField(default=True)
    observaciones    = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.bodega}-{self.pasillo}-{self.modulo}-{self.nivel}"
    
    @property
    def columna(self):
        columna = int(self.modulo)
        return columna


class Movimiento(models.Model):

    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
    tipo            = models.CharField(verbose_name='Tipo de movimiento', choices=TIPOS_MOVIMIENTOS, max_length=10)
    descripcion     = models.CharField(verbose_name='Descripción del movimiento', max_length=20, blank=True)
    referencia      = models.CharField(verbose_name='Referencia del movimiento', choices=REFERENCIA_MOVIMIENTOS, max_length=20, blank=True)
    n_referencia    = models.CharField(verbose_name='Numero de referencia',max_length=20, blank=True)
    n_factura       = models.CharField(verbose_name='Factura despachado',max_length=40, blank=True)
    ubicacion       = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='ubicacion', blank=True, null=True)
    unidades        = models.IntegerField(verbose_name='Unidades ingresadas')
    estado          = models.CharField(verbose_name='Estado Stock', choices=ESTADO, max_length=20, blank=True)
    estado_picking  = models.CharField(verbose_name='Estado Picking', choices=ESTADO_PICKING, max_length=20, blank=True)
    usuario         = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.CASCADE, blank=True, null=True)
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    actualizado     = models.DateTimeField(verbose_name='Fecha Hora Actualización', auto_now=True)

    def __str__(self):
        return self.product_id

    @property
    def enum(self):
        total_registros = Movimiento.objects.filter(id__lte=self.id).count()
        enum = f'{total_registros:06d}'
        return enum 


class Existencias(models.Model):
    
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
    ubicacion       = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='existencias_ubicacion', blank=True, null=True)
    unidades        = models.PositiveIntegerField(verbose_name='Unidades ingresadas')
    estado          = models.CharField(verbose_name='Estado', choices=ESTADO, max_length=20, blank=True)
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    
    def __str__(self):
        return self.product_id
    
    
class Transferencia(models.Model):
    
    doc_gimp        = models.CharField(verbose_name='Doc - GIMPR', max_length=50)
    n_transferencia = models.CharField(verbose_name='Número de trasferencia', max_length=50)
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
    bodega_salida   = models.CharField(verbose_name='Bodega de salida', max_length=10)
    unidades        = models.PositiveIntegerField(verbose_name='Unidades ingresadas')
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    ubicacion       = models.CharField(verbose_name='Ubicacion', max_length=10, blank=True)
    
    def __str__(self):
        return self.n_transferencia
    
    
class TransferenciaStatus(models.Model):
    
    n_transferencia = models.CharField(verbose_name='Número de trasferencia', max_length=50, unique=True)
    unidades_mba    = models.PositiveIntegerField(verbose_name='Unidades mba', default=0)
    unidades_wms    = models.PositiveIntegerField(verbose_name='Unidades wms', default=0)
    avance          = models.FloatField(verbose_name='Avance', default=0.0)
    estado          = models.CharField(verbose_name='Estado', max_length=20)
    
    def __str__(self):
        return self.estado

class LiberacionCuarentena(models.Model):
    doc_id = models.CharField(max_length=255)
    doc_id_corp = models.CharField(max_length=255, primary_key=True)
    product_id_corp = models.CharField(max_length=255)
    product_id= models.CharField(max_length=255)
    lote_id = models.CharField(max_length=255)
    ware_code = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    egreso_temp =  models.CharField(max_length=50)
    commited = models.PositiveIntegerField()
    ware_code_corp = models.CharField(max_length=50)
    ubicacion = models.CharField(max_length=50)
    fecha_elaboracion_lote = models.DateTimeField()
    fecha_caducidad = models.DateTimeField()
    estado = models.PositiveIntegerField()

    # class Meta:
    #     unique_together = (('doc_id_corp', 'product_id_corp', 'lote_id'),)

class NotaEntrega(models.Model):
    
    doc_id_corp     = models.CharField(verbose_name='Doc - GIMPR', max_length=50)
    doc_id          = models.CharField(verbose_name="Doc", max_length=30)
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=50)
    fecha_caducidad = models.DateField(verbose_name='Fecha de caducidad')
    unidades        = models.PositiveIntegerField(verbose_name='Unidades ingresadas')
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)

    def __str__(self):
        return self.doc_id


class NotaEntregaStatus(models.Model):
    
    nota_entrega = models.CharField(verbose_name='Número de nota de entrega', max_length=50, unique=True)
    unidades_mba = models.PositiveIntegerField(verbose_name='Unidades mba', default=0)
    unidades_wms = models.PositiveIntegerField(verbose_name='Unidades wms', default=0)
    avance       = models.FloatField(verbose_name='Avance', default=0.0)
    estado       = models.CharField(verbose_name='Estado', max_length=20)
    
    def __str__(self):
        return self.estado
    

class AnulacionPicking(models.Model):
    
    picking_anulado = models.CharField(verbose_name='Pikcing nulado', max_length=50, unique=True)
    picking_nuevo   = models.CharField(verbose_name='Pikcing nuevo', max_length=50)
    estado          = models.BooleanField(verbose_name='Estado', default=False) 
    usuario         = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.CASCADE, blank=True, null=True)
    fecha_hora      = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    
    
    def __str__(self):
        return self.picking_anulado 
    
    
class AjusteLiberacion(models.Model):
    
    doc_id_corp     = models.CharField(verbose_name='Doc id corp', max_length=255)
    doc_id          = models.CharField(verbose_name='Doc id', max_length=255)
    tipo            = models.CharField(verbose_name='Tipo', choices=TIPO_LIBERACION, max_length=50)
    product_id      = models.CharField(verbose_name='Product id', max_length=255)
    lote_id         = models.CharField(verbose_name='Lote id', max_length=255)
    ware_code       = models.CharField(verbose_name='Bodega', max_length=50)
    location        = models.CharField(verbose_name='Ubicación', max_length=50)
    egreso_temp     = models.PositiveIntegerField(verbose_name='Egreso temp')
    commited        = models.PositiveIntegerField(verbose_name='Commited')
    fecha_caducidad = models.DateField(verbose_name='Fecha caducidad')
    
    unidades_cuc    = models.PositiveIntegerField(verbose_name='Unidades cuarentena', null=True, blank=True)
    ubicacion       = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='ubicacion_cuc_liberacion', blank=True, null=True)
    estado          = models.CharField(verbose_name='Estado', max_length=50, null=True, blank=True)
    
    def __str__(self):
        return self.product_id