# Models
from django.db import models


# Personas
PERSONAS_CHOICES = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
]

# Create your models here.

class Product(models.Model):
    
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    description     = models.CharField(verbose_name='Descripción', max_length=200)
    marca           = models.CharField(verbose_name='Marca', max_length=50)
    marca2          = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    
    unidad_empaque  = models.IntegerField(verbose_name='Unidad Empaque')
    unidad_empaque_box  = models.IntegerField(verbose_name='Unidad Empaque Box', null=True)
    largo           = models.FloatField(verbose_name='Caja master largo (m)', default=0.0, null=True, blank=True)
    ancho           = models.FloatField(verbose_name='Caja master ancho (m)', default=0.0, null=True, blank=True)
    alto            = models.FloatField(verbose_name='Caja master alto (m)', default=0.0, null=True, blank=True)
    volumen         = models.FloatField(verbose_name='Caja master volumen (m3)', default=0.0, null=True, blank=True)
    peso            = models.FloatField(verbose_name='Caja master peso (Kg)', default=0.0, null=True, blank=True)
    t_etiq_1p       = models.FloatField(verbose_name='Tiempo etiq 1 per (s)', default=0.0, null=True, blank=True)
    t_etiq_2p       = models.FloatField(verbose_name='Tiempo etiq 2 per (s)', default=0.0, null=True, blank=True)
    t_etiq_3p       = models.FloatField(verbose_name='Tiempo etiq 3 per (s)', default=0.0, null=True, blank=True)
    t_armado        = models.FloatField(verbose_name='Tiempo armado', default=0.0, null=True, blank=True)

    emp_primario    = models.BooleanField(verbose_name='Empaque primario', default=True, blank=True, null=True)
    emp_secundario  = models.BooleanField(verbose_name='Empaque secundario', default=True, blank=True, null=True)
    emp_terciario   = models.BooleanField(verbose_name='Empaque terciario', default=True, blank=True, null=True)

    n_personas      = models.CharField(verbose_name='Número de personas para etiquetar', max_length=10, choices=PERSONAS_CHOICES, blank=True)

    activo          = models.BooleanField(verbose_name='Producto activo', default=True)
    
    def __str__(self):
        return f'{self.product_id} {self.description} {self.marca}'
    

class Marca(models.Model):
    
    marca   = models.CharField(verbose_name='Marca', max_length=50)
    
    description = models.CharField(verbose_name='Descripción', max_length=200)

    def __str__(self):
        return f'{self.marca} {self.description}'


class MarcaImportExcel(models.Model):
    
    archivo = models.FileField(verbose_name='Archivo Marcas Excel', upload_to='marcas_excel_import')
    
    def __str__(self):
        return str(self.archivo)


class Vehiculos(models.Model):
    
    transportista = models.CharField(verbose_name='Trasportista', max_length=50 ,blank=True)
    placa       = models.CharField(verbose_name='Placa', max_length=50)
    ancho       = models.FloatField(verbose_name='Ancho (m)')
    alto        = models.FloatField(verbose_name='Alto (m)')
    largo       = models.FloatField(verbose_name='Largo (m)')
    volumen     = models.FloatField(verbose_name='Volumen (m3)')
    volumen2    = models.FloatField(verbose_name='Volumen -20% (m3)')
    activo      = models.BooleanField(verbose_name='Activo', default=False)

    def __str__(self):
        return self.placa
    
    
    def save(self, *args, **kwargs):
        self.voluemn  = (self.ancho * self.alto * self.largo)
        self.voluemn2 = self.voluemn * 0.2
        
        return super().save(*args, **kwargs)


class TimeStamp(models.Model):
    
    actulization_stoklote = models.CharField(verbose_name='Actulización Stock Lote', max_length=50)
    actulization_importaciones = models.CharField(verbose_name='Actulización Importaciones', max_length=50, blank=True)
    actulization_stockconsulta = models.CharField(verbose_name='Actulización Importaciones', max_length=50, blank=True)
    actulization_facturas = models.CharField(verbose_name='Actulización Facturas', max_length=50, blank=True)
    actualization_reserva_lote = models.CharField(verbose_name='Reservas lotes', max_length=50, blank=True)
    actualization_imp_llegadas = models.CharField(verbose_name='Importaciones llegadas', max_length=50, blank=True)

    def __str__(self):
        return self.actulization_stoklote


class StockConsulta(models.Model):

    # MBA
    product_id       = models.CharField(verbose_name='Product id', max_length=50, blank=True)
    product_name     = models.CharField(verbose_name='Product name', max_length=200, blank=True)
    group_code       = models.CharField(verbose_name='Group code', max_length=50, blank=True)
    um               = models.CharField(verbose_name='Presentación', max_length=50, blank=True)
    
    oh               = models.IntegerField(verbose_name='OH', blank=True)
    oh2              = models.IntegerField(verbose_name='OH2', blank=True)
    commited         = models.IntegerField(verbose_name='Commited', blank=True)
    quantity         = models.IntegerField(verbose_name='Quantity', blank=True)
    
    lote_id          = models.CharField(verbose_name='Lote', max_length=50, blank=True)
    fecha_elab_lote  = models.DateField(verbose_name='Fecha elaboración lote', blank=True)
    fecha_cadu_lote  = models.DateField(verbose_name='Fecha caducidad lote', blank=True)
    ware_code        = models.CharField(verbose_name='Bodega', max_length=10, blank=True)
    location         = models.CharField(verbose_name='Ubicación', max_length=10, blank=True)

    def __str__(self):
        return self.product_id
    
    
class EmailApiLog(models.Model):
    
    nombre      = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    error       = models.CharField(max_length=250, blank=True, null=True)
    enviado     = models.BooleanField(blank=True, null=True)
    fecha       = models.DateTimeField(auto_now_add=True)


# ADMINISTRACIÓN DE ACTUALIZACIÓNES WAREHOUSE
class AdminActualizationWarehaouse(models.Model):
    
    table_name = models.CharField(max_length=50, unique=True)
    datetime = models.DateTimeField()
    
    def __str__(self):
        return self.table_name