from django.db import models
# from datos.models import Product as MyProduct
# from dataclasses import dataclass

######################################
## MODELO CLIENTES DE GIMPROMED SQL ##
######################################


class Producto(models.Model):
    codigo = models.CharField(
        max_length=100,
        db_column='Codigo',
        primary_key=True
    )
    nombre = models.CharField(
        max_length=200,
        db_column='Nombre'
    )
    marca = models.CharField(
        max_length=100,
        db_column='Marca',
        blank=True,
        null=True
    )
    marca_det = models.CharField(
        max_length=200,
        db_column='MarcaDet',
        blank=True,
        null=True
    )
    unidad = models.CharField(
        max_length=45,
        db_column='Unidad',
        blank=True,
        null=True
    )
    unidad_empaque = models.IntegerField(
        db_column='Unidad_Empaque',
        blank=True,
        null=True
    )
    reg_san = models.CharField(
        max_length=100,
        db_column='Reg_San',
        blank=True,
        null=True
    )
    procedencia = models.CharField(
        max_length=100,
        db_column='Procedencia',
        blank=True,
        null=True
    )
    unidad_box = models.CharField(
        max_length=45,
        db_column='Unidad_Box',
        blank=True,
        null=True
    )
    inactivo = models.IntegerField(
        db_column='Inactivo',
        blank=True,
        null=True
    )
    largo = models.FloatField(
        db_column='Largo',
        blank=True,
        null=True
    )
    ancho = models.FloatField(
        db_column='Ancho',
        blank=True,
        null=True
    )
    altura = models.FloatField(
        db_column='Altura',
        blank=True,
        null=True
    )
    volumen = models.FloatField(
        db_column='Volumen',
        blank=True,
        null=True
    )
    peso = models.FloatField(
        db_column='Peso',
        blank=True,
        null=True
    )
    disponible = models.IntegerField(
        db_column='Disponible',
        blank=True,
        null=True
    )
    unidades_por_pallet = models.IntegerField(
        db_column='UnidadesPorPallet',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'productos'
        managed = False
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        #app_label

    # 🔒 SOLO LECTURA
    def save(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Cliente(models.Model):
    codigo_cliente = models.CharField(
        max_length=100,
        db_column='CODIGO_CLIENTE',
        primary_key=True
    )
    identificacion_fiscal = models.CharField(
        max_length=100,
        db_column='IDENTIFICACION_FISCAL'
    )
    nombre_cliente = models.CharField(
        max_length=200,
        db_column='NOMBRE_CLIENTE'
    )
    ciudad_principal = models.CharField(
        max_length=100,
        db_column='CIUDAD_PRINCIPAL',
        blank=True,
        null=True
    )
    client_type = models.CharField(
        max_length=50,
        db_column='CLIENT_TYPE',
        blank=True,
        null=True
    )
    salesman = models.CharField(
        max_length=50,
        db_column='SALESMAN',
        blank=True,
        null=True
    )
    limite_credito = models.IntegerField(
        db_column='LIMITE_CREDITO',
        blank=True,
        null=True
    )
    pricelist = models.IntegerField(
        db_column='PRICELIST',
        blank=True,
        null=True
    )
    email = models.EmailField(
        max_length=200,
        db_column='EMAIL',
        blank=True,
        null=True
    )
    email_fiscal = models.EmailField(
        max_length=200,
        db_column='Email_Fiscal',
        blank=True,
        null=True
    )
    direccion = models.CharField(
        max_length=200,
        db_column='DIRECCION',
        blank=True,
        null=True
    )
    wp = models.CharField(
        max_length=45,
        db_column='WP',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'clientes'
        managed = False  # CLAVE: Django no crea ni migra la tabla
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    # 🔒 SOLO LECTURA
    def save(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def __str__(self):
        return self.nombre_cliente


class Reserva(models.Model):
    unique_id = models.IntegerField(
        db_column='UNIQUE_ID',
        primary_key=True
    )
    contrato_id = models.CharField(
        max_length=100,
        db_column='CONTRATO_ID'
    )
    fecha_pedido = models.DateField(
        db_column='FECHA_PEDIDO'
    )
    codigo_cliente = models.CharField(
        max_length=100,
        db_column='CODIGO_CLIENTE'
    )
    nombre_cliente = models.CharField(
        max_length=200,
        db_column='NOMBRE_CLIENTE'
    )
    product_id = models.CharField(
        max_length=100,
        db_column='PRODUCT_ID'
    )
    product_name = models.CharField(
        max_length=200,
        db_column='PRODUCT_NAME'
    )
    quantity = models.IntegerField(
        db_column='QUANTITY'
    )
    despachados = models.IntegerField(
        db_column='Despachados',
        blank=True,
        null=True
    )
    ware_code = models.CharField(
        max_length=20,
        db_column='WARE_CODE',
        blank=True,
        null=True
    )
    confirmed = models.IntegerField(
        db_column='CONFIRMED',
        blank=True,
        null=True
    )
    hora_llegada = models.TimeField(
        db_column='HORA_LLEGADA',
        blank=True,
        null=True
    )
    sec_name_cliente = models.CharField(
        max_length=400,
        db_column='SEC_NAME_CLIENTE',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'reservas'
        managed = False
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    # 🔒 SOLO LECTURA
    def save(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def __str__(self):
        return f"{self.fecha_pedido} - {self.nombre_cliente} - {self.product_id}"
