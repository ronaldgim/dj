from django.db import models
import datetime

from users.models import User


# Create your models here.
class DocumentoLote(models.Model):


    o_compra        = models.CharField(verbose_name='Orden de compra', max_length=50, blank=True, null=True)
    product_id      = models.CharField(verbose_name='Código', max_length=50, blank=True, null=True)
    lote_id         = models.CharField(verbose_name='Lote', max_length=50, blank=True, null=True)
    f_caducidad     = models.DateField(verbose_name='F.Caducidad', blank=True, null=True)

    documento       = models.FileField(verbose_name='Documento', upload_to='documentos_lotes', blank=True, null=True)
    
    def __str__(self):
        return self.product_id + ' ' + self.lote_id
    

class DocumentoEnviado(models.Model):
    n_factura      = models.CharField(verbose_name='Factura', max_length=50, blank=True, null=True)
    codigo_cliente = models.CharField(verbose_name='Código cliente', max_length=50, blank=True, null=True)
    nombre_cliente = models.CharField(verbose_name='Nombre cliente', max_length=50, blank=True, null=True)
    correo_cliente = models.EmailField(verbose_name='Correo cliente')
    detalle        = models.TextField(verbose_name='Detalle', blank=True, null=True)

    fecha_hora     = models.DateTimeField(auto_now_add=True, verbose_name='Orden de compra')
    usuario        = models.ForeignKey(User, verbose_name='Usuario', max_length=50, blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.n_factura


class ProductosRegistroSanitario(models.Model):
    
    product_id = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.product_id


class RegistroSanitario(models.Model):
    
    n_reg_sanitario = models.CharField(max_length=50)
    descripcion     = models.CharField(max_length=150)
    fecha_caducidad = models.DateField()
    documento       = models.FileField(upload_to='registros_sanitarios')
    productos       = models.ManyToManyField(ProductosRegistroSanitario, blank=True)
    creado          = models.DateTimeField(auto_now_add=True)
    actualizado     = models.DateTimeField(auto_now=True)
    usuario         = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.PROTECT)
    
    def __str__(self):
        return self.n_reg_sanitario

    @property
    def estado(self):
        return 'Caducado' if self.fecha_caducidad < datetime.date.today() else 'Vigente'


class DocumentosLegales(models.Model):
    
    marca                = models.CharField(max_length=50)
    nombre_proveedor     = models.CharField(max_length=50)
    documento            = models.FileField(upload_to='isos')
    fecha_caducidad      = models.DateField()
    registros_sanitarios = models.ManyToManyField(RegistroSanitario, blank=True)
    creado               = models.DateTimeField(auto_now_add=True)
    actualizado          = models.DateTimeField(auto_now=True)
    usuario              = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.PROTECT)
    
    def __str__(self):
        return self.marca
    
    @property
    def estado(self):
        return 'Caducado' if self.fecha_caducidad < datetime.date.today() else 'Vigente'


class IsosRegEnviados(models.Model):
    
    tipo_documento = models.CharField(max_length=20) # iso o reg sanitario
    descripcion    = models.CharField(max_length=200, blank=True) # marca o product_id
    documento      = models.FileField(upload_to='doc_legales_enviados', blank=True, null=True) # documento con marca de agua 
    creado         = models.DateTimeField(auto_now_add=True)

class FacturaProforma(models.Model):
    
    tipo_comprobante = models.CharField(max_length=10) # factura o proforma
    n_comprobante    = models.CharField(max_length=30) # numero de factura o proforma
    detalle          = models.TextField() # lista de productos JSON
    documentos       = models.ManyToManyField(IsosRegEnviados)   
    codigo_cliente   = models.CharField(max_length=10)
    nombre_cliente   = models.CharField(max_length=150)
    marca_de_agua    = models.TextField(blank=True)
    creado           = models.DateTimeField(auto_now_add=True)
    actualizado      = models.DateTimeField(auto_now=True)
    usuario          = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.PROTECT)
    email            = models.BooleanField(default=False)