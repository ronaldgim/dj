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
    url_descarga   = models.CharField(max_length=300, blank=True) # url de descarga del documento
    # url_descarga   = models.URLField(_(""), max_length=200)
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
    procesar_docs    = models.BooleanField(default=False)
    opacidad         = models.CharField(max_length=2, default='3')
    


class DocumentoVario(models.Model):
    descripcion    = models.CharField(max_length=200)
    codigo_cliente = models.CharField(max_length=50)
    cliente        = models.CharField(max_length=100)
    marca_agua     = models.TextField(blank=True)
    opacidad       = models.CharField(max_length=2, default='3', blank=True)
    email_envio    = models.EmailField(verbose_name='Correo de envío', blank=True, null=True)
    docs_enviados  = models.BooleanField(default=False)
    creado         = models.DateTimeField(auto_now_add=True)
    usuario        = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.PROTECT)
    
    def __str__(self):
        return self.descripcion

    @property
    def enum(self):
        total_docs = DocumentoVario.objects.filter(id__lte=self.id).count()
        return f'{total_docs:03d}'
    
    @property
    def n_docs(self):
        return self.documento_set.count()    
    
    @property
    def docs_procesados(self):
        return all(self.documento_set.values_list('procesado', flat=True))
    
    
class Documento(models.Model):
    documento_vario = models.ForeignKey(DocumentoVario, verbose_name='Documento Vario', on_delete=models.CASCADE)
    documento       = models.FileField(upload_to='documentos_varios')
    tipo            = models.CharField(max_length=50, blank=True) # pdf, jpg, png, etc
    tipo_otro       = models.CharField(max_length=100, blank=True) # descripcion si tipo es otro
    descripcion     = models.CharField(max_length=200, blank=True)
    procesado       = models.BooleanField(default=False)
    url_descarga    = models.CharField(max_length=300, blank=True) # url de descarga del documento
    creado          = models.DateTimeField(auto_now_add=True)
    usuario         = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.PROTECT)
    
    
    def __str__(self):
        return self.documento_vario.descripcion
    
    @property
    def nombre_documento(self):
        return self.documento.name.split('/')[-1]
    