# DB
from django.db import models

# Models
from datos.models import Product
from mantenimiento.models import Equipo
from users.models import UserPerfil, User

# Estado Picking select
ESTADO_PICKING = [
    ('EN PAUSA', 'EN PAUSA'),
    ('EN PROCESO', 'EN PROCESO'),
    ('INCOMPLETO', 'INCOMPLETO'),
    ('FINALIZADO', 'FINALIZADO'),
]

# Create your models here.
class EtiquetadoStock(models.Model):
    
    product_id      = models.CharField(verbose_name='Código', max_length=50)
    product_name    = models.CharField(verbose_name='Nombre', max_length=100)
    product_group   = models.CharField(verbose_name='Marca', max_length=50)
    o_etiq          = models.FloatField(verbose_name='O.Etiquetado')
    reservas        = models.IntegerField(verbose_name='Reserva')
    transito        = models.IntegerField(verbose_name='Trnasito')
    disp_reserva    = models.IntegerField(verbose_name='Desp-Reserva')
    disp_total      = models.IntegerField(verbose_name='Desp-Total')
    mensual         = models.IntegerField(verbose_name='Mensual')
    cuarentena      = models.IntegerField(verbose_name='Cuarentena')
    tres_semanas    = models.IntegerField(verbose_name='3Semanas')
    stock_mensual   = models.IntegerField(verbose_name='StockMensual')
    meses           = models.FloatField(verbose_name='Meses')
    actulizado      = models.CharField(verbose_name='Fecha de aculización', max_length=50, blank=True)
    
    def __str__(self):
        return self.product_id


class RowItem(models.Model):
    
    item = models.ForeignKey(Product, verbose_name='Item', on_delete=models.PROTECT)
    lote = models.CharField(verbose_name='Lote', max_length=100, blank=True)    
    cant = models.IntegerField(verbose_name='Cantidad')
    
    def __str__(self):
        return str(self.item.product_id)
    

class Calculadora(models.Model):
    
    nombre = models.CharField(verbose_name='Nombre', max_length=50)
    prod   = models.ManyToManyField(RowItem, verbose_name='Productos', blank=True)
    
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    
    def __str__(self):
        return self.nombre


class EstadoEtiquetado(models.Model):
    
    estado = models.CharField(verbose_name='Estado', max_length=50)
    
    def __str__(self):
        return self.estado 


class PedidosEstadoEtiquetado(models.Model):
    
    n_pedido = models.CharField(verbose_name='Pedido', max_length=50, unique=True)
    estado   = models.ForeignKey(EstadoEtiquetado, verbose_name='Estado', on_delete=models.CASCADE)
    equipo   = models.ManyToManyField(Equipo, verbose_name='Equipo', blank=True)
    
    fecha_creado = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.n_pedido


class OrdenEtiquetadoStock(models.Model):
    
    cliente = models.CharField(verbose_name='Cliente', max_length=100, default='Gimpromed Cía. Ltda.')
    tipo    = models.CharField(verbose_name='Tipo', max_length=100, default='STOCK')
    ciudad  = models.CharField(verbose_name='Ciudad', max_length=100, default='Cerezos')
    prod   = models.ManyToManyField(RowItem, verbose_name='Productos', blank=True)
    
    fecha_creado = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.cliente


class EstadoPicking(models.Model):
    
    user     = models.ForeignKey(UserPerfil, verbose_name='User', on_delete=models.CASCADE)
    
    n_pedido = models.CharField(verbose_name='Pedido', max_length=50, unique=True)

    # estado   = models.CharField(verbose_name='Estado', max_length=50, choices=ESTADO_PICKING)

    estado   = models.CharField(verbose_name='Estado', max_length=50)

    fecha_pedido = models.CharField(verbose_name='Fecha pedido', max_length=50, blank=True)
    tipo_cliente = models.CharField(verbose_name='Tipo cliente', max_length=50, blank=True)
    cliente = models.CharField(verbose_name='Cliente', max_length=100, blank=True)
    codigo_cliente = models.CharField(verbose_name='Código Cliente', max_length=100, blank=True)
    detalle  = models.TextField(verbose_name='Detalle')
    bodega = models.CharField(verbose_name='Bodega', max_length=50, blank=True)
    
    fecha_creado = models.DateTimeField(auto_now_add=True)
    # fecha_actualizado = models.DateTimeField(auto_now=True)
    fecha_actualizado = models.DateTimeField(verbose_name='Hora actualizado', blank=True, null=True)

    facturado_por  = models.ForeignKey(User, verbose_name='Vendedor', on_delete=models.PROTECT ,blank=True, null=True)
    hora_facturado = models.DateTimeField(verbose_name='Hora de facturación', blank=True, null=True)
    facturado      = models.BooleanField(verbose_name='Facturado', default=False)
    whatsapp       = models.BooleanField(verbose_name='Whatsapp', default=False)
    
    def __str__(self):
        return self.n_pedido



class RegistoGuia(models.Model):

    user          = models.ForeignKey(UserPerfil, verbose_name='User', on_delete=models.CASCADE)

    cliente       = models.CharField(verbose_name='Cliente', max_length=150, blank=True)
    factura       = models.CharField(verbose_name='Factura', max_length=50, blank=True)
    factura_c     = models.CharField(verbose_name='Factura completo', max_length=50, blank=True)
    ciudad        = models.CharField(verbose_name='Ciudad', max_length=50, blank=True)
    fecha_factura = models.DateField(verbose_name='Fecha factura', blank=True)
    
    transporte    = models.CharField(verbose_name='Transporte', max_length=30, blank=True)
    confirmado    = models.CharField(verbose_name='Confirmado por', max_length=50, blank=True)
    fecha_conf    = models.DateField(verbose_name='Fecha confirmación', blank=True)
    n_guia        = models.CharField(verbose_name='Número de guía', max_length=150, blank=True)

    observaciones = models.TextField(verbose_name='Observaciones', blank=True)

    def __str__(self):
        return self.cliente + ' ' + self.factura_c
    


class FechaEntrega(models.Model):
    user          = models.ForeignKey(UserPerfil, verbose_name='User', on_delete=models.CASCADE)
    fecha_hora    = models.DateTimeField(verbose_name='Fecha Hora de Entrega')
    estado        = models.CharField(verbose_name='Esatdo fecha', max_length=30)
    pedido        = models.CharField(verbose_name='pedido', max_length=15, unique=True)

    est_entrega       = models.CharField(verbose_name='Esatdo entrega', blank=True, max_length=30)
    reg_entrega   = models.ForeignKey(UserPerfil, verbose_name='User entrega', blank=True, null=True, on_delete=models.CASCADE, related_name='usuario_entrega')

    def __str__(self):
        return self.pedido + ' ' + self.estado
    


class ProductArmado(models.Model):
    
    producto = models.ForeignKey(Product, verbose_name='Producto', blank=True, on_delete=models.CASCADE)
    activo   = models.BooleanField(verbose_name='activo', default=True)

    def __str__(self):
        return f"{self.producto}, {self.activo}"
    
    
class InstructivoEtiquetado(models.Model):
    
    equipo        = models.ForeignKey(Equipo, verbose_name='Equipo', on_delete=models.CASCADE)
    producto      = models.ForeignKey(Product, verbose_name='Producto', on_delete=models.CASCADE)
    foto          = models.ImageField(verbose_name='Foto', upload_to='instructivo-etiquetado', blank=True, null=True)
    observaciones = models.CharField(verbose_name='observaciones', blank=True, max_length=150)
    
    creado  = models.DateTimeField(verbose_name='Creado', auto_now_add=True)
    
    def __str__(self):
        return f'{self.equipo} - {self.producto}' 
    
    
class EtiquetadoAvance(models.Model):
    
    n_pedido   = models.CharField(verbose_name='N°. Pedido', blank=True, max_length= 10)
    product_id = models.CharField(verbose_name='Product id', blank=True, max_length=50)
    unidades   = models.IntegerField(verbose_name='Unidades', blank=True)
    
    def __str__(self):
        return f'{self.n_pedido} - {self.product_id}'
    
    
class EstadoEtiquetadoStock(models.Model):
    
    product_id = models.CharField(verbose_name='Código', max_length=15, blank=True)
    estado     = models.CharField(verbose_name='Estado', max_length=15, blank=True)
    
    creado     = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.product_id