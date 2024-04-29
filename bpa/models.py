# Models
from django.db import models

# Datetime
from datetime import datetime, date, timedelta

DOC = [
    ('Electrónico', 'Electrónico'),
    ('Fisíco', 'Fisíco')
]



# Muestreos Transferencias
class Trasferencia(models.Model):

    documento       = models.CharField(verbose_name='Documeto', max_length=50)
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    lote            = models.CharField(verbose_name='Lote', max_length=50)
    unidades        = models.IntegerField(verbose_name='Unidades')
    
    def __str__(self):
        return self.documento


# Registro Sanitario LEG-REG
class RegistroSanitario(models.Model):
    
    marca            = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    propietario      = models.CharField(verbose_name='Propietario', default='Gimpromed. Cia. Ltda.', max_length=50, blank=True)
    documento       = models.CharField(verbose_name='Documento', choices=DOC, default=DOC[0][0] ,max_length=50)
    registro         = models.CharField(verbose_name='Reg. Sanitario', max_length=50) #, unique=True)
    producto         = models.TextField(verbose_name='Producto Denominado', blank=True)
    origen           = models.CharField(verbose_name='Origen Fabricante', max_length=50, blank=True)
    imp_desde        = models.CharField(verbose_name='Importado desde', max_length=50, blank=True)
    fecha_expedicion = models.DateField(verbose_name='Fecha de expedición', blank=True, null=True)
    fecha_expiracion = models.DateField(verbose_name='Fecha de expiración', blank=True, null=True)
    lugar_archivo    = models.CharField(verbose_name='Importado desde', max_length=50, blank=True)
    cn_recomen       = models.IntegerField(verbose_name='Copias Notariadas Recomendadas', default=0, blank=True, null=True)
    cn_carpeta       = models.IntegerField(verbose_name='Copias Notariadas Carpeta', default=0, blank=True, null=True)
    fecha_notaria    = models.DateField(verbose_name='Fecha de envio a notaria', blank=True, null=True)
    notaria          = models.CharField(verbose_name='Notaria', max_length=50, blank=True)
    codigo           = models.CharField(verbose_name='Código', max_length=50, blank=True)
    n_solicitud      = models.CharField(verbose_name='Número Solicitud', max_length=50, blank=True)
    n_emision        = models.CharField(verbose_name='Número de emisión', max_length=50, blank=True)
    observacion      = models.TextField(verbose_name='Observaciones', blank=True)
    activo           = models.BooleanField(verbose_name='Activo', default=True)
    
    def __str__(self):
        return f'{self.id} - {self.marca} - {self.registro}'

    @property
    def estado(self):
        seis_meses = timedelta(365/2)

        if self.fecha_expiracion == None:
            estado = 'Sin especificar'
        elif self.fecha_expiracion < date.today():
            estado = 'Caducado'
        elif (self.fecha_expiracion - seis_meses) <= date.today():
            estado = 'Próximo a caducar'
        elif (self.fecha_expiracion - seis_meses) > date.today():
            estado = 'Vigente'

        return estado


    @property
    def obs_doc(self):

        if self.cn_carpeta < self.cn_recomen:
            obs_doc = 'Enviar a notaria'
        else:
            obs_doc = 'Docs ok'

        return obs_doc


    @property
    def dias_caducar(self):
        if self.fecha_expiracion is None:
            dias = 0
        else:
            dias = (self.fecha_expiracion - date.today()).days
            if dias < 0:
                dias = 0
            else:
                dias = dias

        return dias


# Carta no registro
class CartaNoRegistro(models.Model):
    
    marca            = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    documento        = models.CharField(verbose_name='Documento', choices=DOC, default=DOC[0][0], max_length=50)
    n_solicitud      = models.CharField(verbose_name='Número Solicitud', max_length=50, blank=True)
    producto         = models.TextField(verbose_name='Producto Denominado', blank=True)
    fecha_expedicion = models.DateField(verbose_name='Fecha de expedición', blank=True, null=True)
    fecha_expiracion = models.DateField(verbose_name='Fecha de expiración', blank=True, null=True)
    observacion      = models.TextField(verbose_name='Observaciones', blank=True)
    
    def __str__(self):
        return f'{self.id} - {self.marca} - {self.producto}'


    @property
    def estado(self):
        seis_meses = timedelta(365/2)

        if self.fecha_expiracion == None:
            estado = 'Sin especificar'
        elif self.fecha_expiracion < date.today():
            estado = 'Caducado'
        elif (self.fecha_expiracion - seis_meses) <= date.today():
            estado = 'Próximo a caducar'
        elif (self.fecha_expiracion - seis_meses) > date.today():
            estado = 'Vigente'

        return estado


    @property
    def dias_caducar(self):
        if self.fecha_expiracion is None:
            dias = int(dias)
            dias = 0
        else:
            dias = (self.fecha_expiracion - date.today()).days
            if dias < 0:
                dias = 0
            else:
                dias = dias
        return dias
