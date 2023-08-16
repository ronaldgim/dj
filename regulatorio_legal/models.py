from django.db import models

from users.models import User

# Create your models here.


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
