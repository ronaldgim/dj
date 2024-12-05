# Models
from django.db import models

# Peril
from users.models import User

# Time
from datetime import timedelta, date

# Models
from datos.models import Product


# Inventario
class Inventario(models.Model):

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
    
    # Inventario Físico
    unidades_caja    = models.IntegerField(verbose_name='Unidades por caja', blank=True)  # default = 0
    numero_cajas     = models.IntegerField(verbose_name='Número de cajas', blank=True)  # default = 0
    unidades_sueltas = models.IntegerField(verbose_name='Unidades sueltas', blank=True)  # default = 0
    total_unidades   = models.IntegerField(verbose_name='Total de unidades', blank=True)  # default = 0
    diferencia       = models.IntegerField(verbose_name='Diferencia', blank=True)  # default = 0
    observaciones    = models.CharField(verbose_name='Observaciones', max_length=100, blank=True)

    # De control
    llenado = models.BooleanField(verbose_name='Llenado', default=False)
    agregado = models.BooleanField(verbose_name='Añadido', default=False)

    # Usuario
    user     = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.product_id

    def save(self, *args, **kwargs):
        self.total_unidades = (self.unidades_caja * self.numero_cajas) + self.unidades_sueltas
        self.diferencia = self.total_unidades - self.oh2
        return super().save(*args, **kwargs)


class InventarioTotale(models.Model):

    # MBA
    product_id_t       = models.CharField(verbose_name='Product id', max_length=50, blank=True)
    ware_code_t        = models.CharField(verbose_name='Bodega', max_length=10, blank=True)
    location_t         = models.CharField(verbose_name='Ubicación', max_length=10, blank=True)
    
    # Inventario Físico
    unidades_caja_t    = models.IntegerField(verbose_name='Unidades por caja', blank=True)
    numero_cajas_t     = models.IntegerField(verbose_name='Número de cajas', blank=True)
    unidades_sueltas_t = models.IntegerField(verbose_name='Unidades sueltas', blank=True)

    total_unidades_t   = models.IntegerField(verbose_name='Total de unidades', blank=True, null=True)

    user     = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.product_id_t

    def save(self, *args, **kwargs):
        self.total_unidades_t = (self.unidades_caja_t * self.numero_cajas_t) + self.unidades_sueltas_t
        return super().save(*args, **kwargs)
    

# Inventario Cerezos
from wms.models import Ubicacion
class InventarioCerezos(models.Model):

    # MBA
    product_id       = models.CharField(verbose_name='Product id', max_length=50, blank=True)
    product_name     = models.CharField(verbose_name='Product name', max_length=200, blank=True)
    group_code       = models.CharField(verbose_name='Group code', max_length=50, blank=True)
    um               = models.CharField(verbose_name='Presentación', max_length=50, blank=True)
    estado           = models.CharField(verbose_name='Estado', max_length=20, blank=True)
    
    oh2              = models.IntegerField(verbose_name='OH2', blank=True)
    
    lote_id          = models.CharField(verbose_name='Lote', max_length=50, blank=True)
    fecha_elab_lote  = models.DateField(verbose_name='Fecha elaboración lote', blank=True)
    fecha_cadu_lote  = models.DateField(verbose_name='Fecha caducidad lote', blank=True)
    ubicacion       = models.ForeignKey(Ubicacion, verbose_name='Ubicación', max_length=5, on_delete=models.CASCADE, related_name='inventario_ubicacion', blank=True, null=True)
    
    # Inventario Físico
    unidades_caja    = models.IntegerField(verbose_name='Unidades por caja', blank=True)  # default = 0
    numero_cajas     = models.IntegerField(verbose_name='Número de cajas', blank=True)  # default = 0
    unidades_sueltas = models.IntegerField(verbose_name='Unidades sueltas', blank=True)  # default = 0
    total_unidades   = models.IntegerField(verbose_name='Total de unidades', blank=True)  # default = 0
    diferencia       = models.IntegerField(verbose_name='Diferencia', blank=True)  # default = 0
    observaciones    = models.CharField(verbose_name='Observaciones', max_length=100, blank=True)

    # De control
    llenado = models.BooleanField(verbose_name='Llenado', default=False)
    agregado = models.BooleanField(verbose_name='Añadido', default=False)

    # Usuario
    user     = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.product_id

    def save(self, *args, **kwargs):
        self.total_unidades = (self.unidades_caja * self.numero_cajas) + self.unidades_sueltas
        self.diferencia = self.total_unidades - self.oh2
        return super().save(*args, **kwargs)

# Arqueos
class Arqueo(models.Model):

    descripcion = models.TextField(verbose_name='Descripción', max_length=50)
    productos   = models.ManyToManyField(Product, verbose_name='Productos', blank=True)

    fecha_hora  = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    usuario     = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f'{self.id}'
    

    @property
    def enum(self):
        
        n_len = len(str(self.id))
        nn = str(self.id)

        if n_len == 3:
            n = nn

        elif n_len == 2:
            n = '0'+nn

        elif n_len == 1:
            n = '00'+nn

        else:
            n = nn
        
        return n
    

# Arqueo toma fisica
class ArqueoFisico(models.Model):

    # Arqueo
    id_arqueo        = models.IntegerField(verbose_name='Arqueo', blank=True)

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
    
    # Inventario Físico
    unidades_caja    = models.IntegerField(verbose_name='Unidades por caja', blank=True, default=0)
    numero_cajas     = models.IntegerField(verbose_name='Número de cajas', blank=True, default=0)
    unidades_sueltas = models.IntegerField(verbose_name='Unidades sueltas', blank=True, default=0)
    total_unidades   = models.IntegerField(verbose_name='Total de unidades', blank=True, default=0)
    diferencia       = models.IntegerField(verbose_name='Diferencia', blank=True, default=0)
    observaciones    = models.CharField(verbose_name='Observaciones', max_length=100, blank=True)
    observaciones2   = models.CharField(verbose_name='Observaciones2', max_length=100, blank=True)

    # De control
    llenado = models.BooleanField(verbose_name='Llenado', default=False)
    agregado = models.BooleanField(verbose_name='Añadido', default=False)

    # Usuario
    user     = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.CASCADE)


    def __str__(self):
        return f"arqueo: {self.id_arqueo}, producto: {self.product_id}"
    


class ArqueosCreados(models.Model):

    arqueo      = models.ForeignKey(Arqueo, verbose_name='Arqueo', blank=True, null=True, on_delete=models.DO_NOTHING) ###
    arqueo_enum = models.CharField(verbose_name='N° Arqueo', max_length=100, blank=True)

    ware_code   = models.CharField(verbose_name='Bodega código', max_length=100, blank=True)
    bodega      = models.CharField(verbose_name='Bodega', max_length=100, blank=True)
    descripcion = models.TextField(verbose_name='Descripción', max_length=50)
    
    estado      = models.CharField(verbose_name='Estado', max_length=100, blank=True)

    reservas    = models.TextField(verbose_name='Reservas', blank=True)
    reservas_sinlote    = models.TextField(verbose_name='Reservas sin lote', blank=True)

    fecha_hora  = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    fecha_hora_actualizado = models.DateTimeField(auto_now=True)
    usuario     = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"id: {self.id}, arqueo: {self.arqueo_enum}, estado: {self.estado}"


