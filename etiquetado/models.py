# DB
from django.db import models

# Models
from datos.models import Product, Vehiculos
from mantenimiento.models import Equipo
from users.models import UserPerfil , User

#from datos.views import productos_odbc_and_django

# Estado Picking select
ESTADO_PICKING = [
    ('EN PAUSA', 'EN PAUSA'),
    ('EN PROCESO', 'EN PROCESO'),
    ('INCOMPLETO', 'INCOMPLETO'),
    ('FINALIZADO', 'FINALIZADO'),
]


BODEGA_NOMBRE = [
    ('Andagoya', 'Andagoya'),
    ('Cerezos', 'Cerezos'),
]

ESTADO_PEDIDO_TEMPORAL = [
    ('PENDIENTE', 'PENDIENTE'),
    ('CERRADO', 'CERRADO'),
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
    estado   = models.CharField(verbose_name='Estado', max_length=50)
    fecha_pedido = models.CharField(verbose_name='Fecha pedido', max_length=50, blank=True)
    tipo_cliente = models.CharField(verbose_name='Tipo cliente', max_length=50, blank=True)
    cliente = models.CharField(verbose_name='Cliente', max_length=100, blank=True)
    codigo_cliente = models.CharField(verbose_name='Código Cliente', max_length=100, blank=True)
    detalle  = models.TextField(verbose_name='Detalle')
    bodega = models.CharField(verbose_name='Bodega', max_length=50, blank=True)
    fecha_creado = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(verbose_name='Hora actualizado', blank=True, null=True)
    facturado_por  = models.ForeignKey(User, verbose_name='Vendedor', on_delete=models.PROTECT ,blank=True, null=True)
    hora_facturado = models.DateTimeField(verbose_name='Hora de facturación', blank=True, null=True)
    facturado      = models.BooleanField(verbose_name='Facturado', default=False)
    whatsapp       = models.BooleanField(verbose_name='Whatsapp', default=False)
    wh_fail_number = models.BooleanField(verbose_name='Wh numero sin +593', default=False)
    foto_picking   = models.ImageField(upload_to='picking', null=True, blank=True)
    foto_picking_2 = models.ImageField(upload_to='picking', null=True, blank=True)
    noti_errors    = models.TextField(blank=True)
    noti_detalles  = models.TextField(blank=True)
    n_factura      = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.n_pedido
    
    @property
    def bodega_str(self):
        if self.bodega == 'BAN':
            return 'Andagoya'
        elif self.bodega  == 'BCT':
            return 'Cerezos'
        else:
            return ''
    
    @property
    def facturado_por_str(self):
        if self.facturado_por:
            return f'{self.facturado_por.first_name} {self.facturado_por.last_name}'
        return ''
    
    @property
    def fecha_notificado(self):
        if self.hora_facturado:
            return self.hora_facturado.strftime('%Y-%m-%d %H:%M')
        else:
            return '-'


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
    
    
class AnexoDoc(models.Model):

    transporte     = models.CharField(max_length=20, blank=True)
    n_guia         = models.CharField(max_length=120, blank=True)
    tipo_contenido = models.CharField(max_length=20, blank=True)
    contenido      = models.CharField(max_length=10)
    
    def __str__(self):
        return self.n_guia
    
class AnexoGuia(models.Model):
    
    version_documento = models.CharField(max_length=3, default='02')
    bodega_nombre     = models.CharField(max_length=20, choices=BODEGA_NOMBRE)
    bodega_codigo     = models.CharField(max_length=2)
    estado            = models.CharField(max_length=20, default='Incompleto')
    user              = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE)
    contenido         = models.ManyToManyField(AnexoDoc)
    creado            = models.DateField(auto_now_add=True)
    
    @property
    def numero_anexo(self):
        n = int(self.id)
        bodega = self.bodega_codigo
        anio   = self.creado.year - 2000
        return f'{bodega}-{anio}-{n:03d}'
    
    def __str__(self):
        return self.numero_anexo


class FechaEntrega(models.Model):
    user          = models.ForeignKey(UserPerfil, verbose_name='User', on_delete=models.CASCADE)
    fecha_hora    = models.DateTimeField(verbose_name='Fecha Hora de Entrega')
    estado        = models.CharField(verbose_name='Esatdo fecha', max_length=30)
    pedido        = models.CharField(verbose_name='pedido', max_length=15, unique=True)
    est_entrega   = models.CharField(verbose_name='Esatdo entrega', blank=True, max_length=30)
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


class AddEtiquetadoPublico(models.Model):
    
    contrato_id = models.CharField(max_length=10)



# UBICACIONES DE BODEGA ANDAGOYA
BODEGA = [
    ('AN1', 'AN1'),
    ('AN4', 'AN4'),
    ('BN1', 'BN1'),
    ('BN2', 'BN2'),
    ('BN3', 'BN3'),
    ('BN4', 'BN4'),
]

PASILLO_BLOQUE = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
    ('F', 'F'),
    ('G', 'G'),
    ('H', 'H'),
    ('I', 'I'),
    ('J', 'J'),
]
class UbicacionAndagoya(models.Model):
    
    bodega     = models.CharField(verbose_name='Bodega', choices=BODEGA, max_length=10)
    pasillo    = models.CharField(verbose_name='Pasillo/Bloque', choices=PASILLO_BLOQUE, max_length=10)
    modulo     = models.CharField(verbose_name='Modulo', max_length=10, blank=True)
    nivel      = models.CharField(verbose_name='Nivel', max_length=10, blank=True)
    estanteria = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('bodega', 'pasillo', 'modulo', 'nivel')
    
    
    def __str__(self):
        
        if self.estanteria:
            return f'{self.bodega}-{self.pasillo}-{self.modulo}-{self.nivel}'
        else:   
            return f'{self.bodega}-{self.pasillo}'
    
    
    @property
    def nombre(self):
        if self.estanteria:
            return f"{self.bodega}-{self.pasillo}-{self.modulo}-{self.nivel}"
        else:
            return f"{self.bodega}-{self.pasillo}"
    
    
class ProductoUbicacion(models.Model):
    
    product_id = models.CharField(verbose_name='ID del Producto', max_length=50, unique=True )
    ubicaciones = models.ManyToManyField('UbicacionAndagoya', verbose_name='Ubicaciones',related_name='productos')

    def __str__(self):
        ubicaciones_str = ", ".join([f"{ubicacion.bodega}-{ubicacion.pasillo}-{ubicacion.modulo}-{ubicacion.nivel}" for ubicacion in self.ubicaciones.all()])
        return f"Producto: {self.product_id} | Ubicaciones: {ubicaciones_str}"
    
    # @property
    # def ubicaciones_str(self):


class ProductosPedidoTemporal(models.Model):
    
    product_id = models.CharField(max_length=50)
    cantidad   = models.IntegerField()
    
    def __str__(self):
        return self.product_id


class PedidoTemporal(models.Model):
    
    cliente   = models.CharField(max_length=100)
    ruc       = models.CharField(max_length=15)
    estado    = models.CharField(max_length=20, choices=ESTADO_PEDIDO_TEMPORAL)
    entrega   = models.DateTimeField(blank=True, null=True)
    productos = models.ManyToManyField(ProductosPedidoTemporal, blank=True)
    creado    = models.DateTimeField(auto_now_add=True)
    usuario   = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE)
    
    @property
    def enum(self):
        total_registros = PedidoTemporal.objects.filter(id__lte=self.id).count()
        enum = f'PT-{total_registros:03d}'
        return enum 
