# Models
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Personas
PERSONAS_CHOICES = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
]

# Create your models here.

class Product(models.Model):
    
    product_id      = models.CharField(verbose_name='Product id', max_length=50)
    description     = models.CharField(verbose_name='Descripción', max_length=200, blank=True)
    marca           = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    marca2          = models.CharField(verbose_name='Marca', max_length=50, blank=True)
    
    unidad_empaque  = models.IntegerField(verbose_name='Unidad Empaque', default=0, blank=True)
    unidad_empaque_box  = models.IntegerField(verbose_name='Unidad Empaque Box', default=0, null=True, blank=True)
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
    
    class Meta:
        ordering = ('product_id',)
    

class Marca(models.Model):
    
    marca   = models.CharField(verbose_name='Marca', max_length=50)
    description = models.CharField(verbose_name='Descripción', max_length=200)

    def __str__(self):
        return f'{self.marca} {self.description}'


# class MarcaImportExcel(models.Model):
    
#     archivo = models.FileField(verbose_name='Archivo Marcas Excel', upload_to='marcas_excel_import')
    
#     def __str__(self):
#         return str(self.archivo)


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
    automatico = models.BooleanField(default=False)
    periodicidad = models.CharField(max_length=20, blank=True)
    milisegundos = models.IntegerField(null=True)
    orden = models.IntegerField(null=True)
    mensaje = models.TextField(blank=True)
    conexion = models.CharField(max_length=15, blank=True, default='api')
    
    def __str__(self):
        return self.table_name


class Reservas(models.Model):
    
    contrato_id      = models.CharField(max_length=20, blank=True)
    codigo_cliente   = models.CharField(max_length=20, blank=True)
    product_id       = models.CharField(max_length=30, blank=True)
    quantity         = models.IntegerField(default=0)
    ware_code        = models.CharField(max_length=5, blank=True)
    confirmed        = models.IntegerField(default=0)
    fecha_pedido     = models.DateField(null=True)
    hora_llegada     = models.TimeField(null=True)
    #sec_name_cliente = models.CharField(max_length=255, blank=True)
    sec_name_cliente = models.TextField(blank=True)
    unique_id        = models.BigIntegerField(blank=True, null=True)
    alterado         = models.BooleanField(default=False)
    creado           = models.DateField(auto_now_add=True)
    actualizado      = models.DateField(auto_now=True)
    usuario          = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"unique_id: {self.unique_id} - contrato_id: {self.contrato_id}"


class ErrorLoteReporte(models.Model):
    
    product_id = models.CharField(max_length=50)
    nombre = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    unds_total = models.IntegerField(default=0) #OH
    unds_lotes = models.IntegerField(default=0) #OH2
    unds_transf = models.IntegerField(default=0) #OH_TRANSF
    unds_total_mas_transf = models.IntegerField(default=0) #OH2_MAS_TRANSF
    unds_diff = models.IntegerField(default=0) 
    commited_negativo = models.CharField(blank=True, max_length=5)
    
    def __str__(self):
        return self.product_id

class ErrorLoteDetalle(models.Model):
    
    product_id = models.CharField(max_length=50)
    lote_id = models.CharField(max_length=50)
    oh = models.IntegerField(default=0) #OH
    oh2 = models.IntegerField(default=0) #OH2
    oh_transf = models.IntegerField(default=0) #OH_TRANSF
    diff = models.IntegerField(default=0) 
    commited_negativo = models.CharField(blank=True, max_length=5)
    error = models.BooleanField(default=False)
    
    def __str__(self):
        return self.product_id


class ErrorLoteV2(models.Model):
    
    product_id = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    marca = models.CharField(max_length=30, blank=True, null=True)
    lote_id = models.CharField(max_length=50)
    bodega = models.CharField(max_length=20, blank=True)
    ubicacion = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(default=0)
    available = models.IntegerField(default=0)
    diff_available = models.IntegerField(default=0)
    commited = models.IntegerField(default=0)
    error = models.CharField(max_length=200)
    error_commited = models.BooleanField(default=False)
    error_available = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.product_id} - {self.nombre} - {self.marca}'


class PickingEstadistica(models.Model):
    
    # Número de contrato o pedido | EstadoPicking - default.etiquetado
    contrato_id = models.CharField(max_length=7, unique=True) 
    
    # Estado de picking | EstadoPicking - default.etiquetado
    estado = models.CharField(max_length=15, blank=True)
    
    # Fecha y hora de creación en el sistema MBA | Pedidos - warehouse.pedidos 
    creado_mba = models.DateTimeField(blank=True, null=True) 
    
    # Año creado
    anio_creado = models.PositiveIntegerField(default=0)
    
    # Mes creado
    mes_creado = models.PositiveIntegerField(default=0)
    
    # Día creado
    dia_creado = models.PositiveIntegerField(default=0)
    
    # Dia de la semana creado
    dia_semana_creado = models.PositiveSmallIntegerField(blank=True, null=True)
    
    # Dia de la semana creado string
    dia_semana_creado_str = models.CharField(max_length=10, blank=True, null=True)
    
    # Bodega | EstadoPicking - default.etiquetado
    bodega = models.CharField(max_length=5, blank=True, null=True)
    
    # Usuario que creó el pedido en MBA | Pedidos - warehouse.pedidos
    creado_por_mba = models.CharField(max_length=50, blank=True)
    
    # Username del usuario que creó el pedido en MBA | Query para obtner username de django
    creado_por_mba_username = models.CharField(max_length=50, blank=True)
    
    # Codigo cliente | EstadoPicking - default.etiquetado
    codigo_cliente = models.CharField(max_length=20, blank=True)
    
    # Nombre cliente | EstadoPicking - default.etiquetado
    nombre_cliente = models.CharField(max_length=255, blank=True)
    
    # Tipo cliente | EstadoPicking - default.etiquetado
    tipo_cliente = models.CharField(max_length=50, blank=True)
    
    # Ciudad cliente | Warehouse
    ciudad_cliente = models.CharField(max_length=50, blank=True)
    
    # Fecha y hora de inicio del picking | EstadoPicking - default.etiquetado
    inicio_picking = models.DateTimeField(blank=True, null=True)
    
    # Fecha y hora de fin del picking | EstadoPicking - default.etiquetado
    fin_picking = models.DateTimeField(blank=True, null=True)

    # Numero de factura 
    numero_factura = models.CharField(max_length=15, blank=True)
    
    # Fecha y hora de facturación
    fecha_facturacion = models.DateTimeField(blank=True, null=True)

    # Total de ítems en el picking | EstadoPicking - default.etiquetado
    total_items = models.PositiveIntegerField(default=0)
    
    # Total volumen en m3 del picking | EstadoPicking - default.etiquetado
    total_volumen_m3 = models.FloatField(default=0.0)
    
    # Total peso en Kg del picking | EstadoPicking - default.etiquetado
    total_peso_kg = models.FloatField(default=0.0)
    
    # Usuario que realizó el picking | EstadoPicking - default.etiquetado
    usuario_picking = models.CharField(max_length=50, blank=True)
    
    # Tiempo de creacion a inicio picking 
    tiempo_creacion_a_inicio = models.FloatField(blank=True, null=True)
    
    # Tiempo de inicio a fin picking
    tiempo_inicio_a_fin = models.FloatField(blank=True, null=True)
    
    # Tiempo de finalizado a facturación
    tiempo_fin_a_facturacion = models.FloatField(blank=True, null=True)
    
    # Tiempo total de proceso
    tiempo_total_proceso = models.FloatField(blank=True, null=True)
    
    # Datos completos
    datos_completos = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=["anio_creado", "mes_creado"]),
            models.Index(fields=["bodega"]),
            models.Index(fields=["tipo_cliente"]),
            models.Index(fields=["usuario_picking"]),
        ]
    
    def __str__(self):
        return self.contrato_id
    
    def comprobar_datos_completos(self) -> bool:
        """
        Determina si el registro tiene datos suficientes
        para ser considerado COMPLETO y usable en dashboards
        """

        # Campos que NO pueden ser None
        campos_not_null = [
            self.contrato_id,
            self.creado_mba,
            self.bodega,
            self.codigo_cliente,
            self.nombre_cliente,
            self.tipo_cliente,
            self.inicio_picking,
            self.fin_picking,
            self.fecha_facturacion,
            self.usuario_picking,
            self.tiempo_total_proceso,
        ]

        if any(campo is None for campo in campos_not_null):
            return False

        # Campos string que no pueden ser vacíos
        campos_string_no_vacios = [
            self.creado_por_mba,
            self.creado_por_mba_username,
            self.numero_factura,
        ]

        if any(not str(campo).strip() for campo in campos_string_no_vacios):
            return False

        # Campos numéricos que deben ser > 0
        campos_numericos_positivos = [
            self.total_items,
            self.total_volumen_m3,
            self.total_peso_kg,
            self.tiempo_total_proceso,
        ]

        if any(campo <= 0 for campo in campos_numericos_positivos):
            return False

        return True

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")

        self.datos_completos = self.comprobar_datos_completos()

        if update_fields:
            kwargs["update_fields"] = set(update_fields) | {"datos_completos"}

        super().save(*args, **kwargs)
