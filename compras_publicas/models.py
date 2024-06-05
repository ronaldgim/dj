from django.db import models


# Choices resultado_proceso
RESULTADO = [
    ('GANADO', 'GANADO'),
    ('PERDIDO', 'PERDIDO'),
    ('NO CALIFICADO', 'NO CALIFICADO'),
    ('NO PARTICIPADO', 'NO PARTICIPADO'),
]

# Create your models here.
class EvaluacionProcesos(models.Model):

    codigo_proceso          = models.CharField(verbose_name='Código de procesos', max_length=50, blank=True)
    # Cliente desde tabla de clientes FILTRADO POR HOPITAL PUBLICO
    entidad                 = models.CharField(verbose_name='Entidad', max_length=300, blank=True)
    # SELECCIONAR FECHA
    fecha                    = models.DateField(verbose_name='Fecha', blank=True)
    presupuesto_referencial = models.FloatField(verbose_name='Presupuesto referencial', blank=True, null=True)
    valor_adjudicado        = models.FloatField(verbose_name='Valor adjuntidado', blank=True, null=True)
    # QUE DIJETE EL USUARIO
    insumos_participantes   = models.TextField(verbose_name='Insumos participantes', blank=True)
    resultado_proceso       = models.CharField(verbose_name='Resultado del proceso', max_length=50, choices=RESULTADO, blank=True)
    # QUE DIJITE USUARIO
    empresa_ganadora        = models.CharField(verbose_name='Empresa ganadora', max_length=100, blank=True)
    observaciones           = models.TextField(verbose_name='Observaciones', blank=True)

    def __str__(self):
        return self.codigo_proceso
    

class ProcesosSercop(models.Model):
    
    proceso     = models.CharField(verbose_name='Poroceso', unique=True, max_length=100)
    fecha_hora  = models.DateTimeField(verbose_name='Fecha Hora', auto_now_add=True)
    
    def __str__(self):
        return self.proceso



class Producto(models.Model):
    
    product_id      = models.CharField(verbose_name='Código', max_length=15)
    nombre          = models.CharField(verbose_name='Nombre', max_length=150)
    nombre_generico = models.CharField(verbose_name='Nombre generico', max_length=150, blank=True)
    presentacion    = models.CharField(verbose_name='Presentación', max_length=15, blank=True)
    marca           = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    procedencia     = models.CharField(verbose_name='Procedencia', max_length=50, blank=True)
    r_sanitario     = models.CharField(verbose_name='Registro Sanitario', max_length=50, blank=True)
    lote_id         = models.CharField(verbose_name='Lote', max_length=15)
    f_elaboracion   = models.DateField(verbose_name='Fecha elaboración', blank=True)
    f_caducidad     = models.DateField(verbose_name='Fecha caducidad', blank=True)
    cantidad        = models.IntegerField(verbose_name='Cantidad', blank=True, default=0)
    cantidad_total  = models.IntegerField(verbose_name='Cantidad total', blank=True, default=0)
    precio_unitario = models.FloatField(verbose_name='Precio unitario', blank=True, default=0)
    precio_total    = models.FloatField(verbose_name='Precio total', blank=True, default=0)
    
    def __str__(self):
        return f'{self.id}-{self.product_id}'

class Anexo(models.Model):
    
    n_pedido     = models.CharField(verbose_name='Picking', max_length=10)
    fecha        = models.DateField(verbose_name='Fecha')
    cliente      = models.CharField(verbose_name='Cliente', max_length=150)
    ruc          = models.CharField(verbose_name='Ruc', max_length=13)
    direccion    = models.CharField(verbose_name='Dirección', max_length=150, blank=True)
    orden_compra = models.CharField(verbose_name='Orden de compra', max_length=50, blank=True)
    observaciones = models.TextField(verbose_name='Observaciones', blank=True)
    
    product_list = models.ManyToManyField(Producto)
    
    def __str__(self):
        return self.n_pedido
    