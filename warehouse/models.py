from django.db import models
from datetime import date
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
        # app_label = 'gimpromed_sql'
        app_label = 'warehouse'

    # SOLO LECTURA
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
        # app_label = 'gimpromed_sql'
        app_label = 'warehouse'

    # SOLO LECTURA
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
        # app_label = 'gimpromed_sql'
        app_label = 'warehouse'

    # SOLO LECTURA
    def save(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def __str__(self):
        return f"{self.fecha_pedido} - {self.nombre_cliente} - {self.product_id}"


class CuentasCobrar(models.Model):

    codigo_factura = models.CharField(
        max_length=255,
        primary_key=True,
        db_column='CODIGO_FACTURA'
    )

    numero_factura = models.CharField(
        max_length=50,
        db_column='NUMERO_FACTURA',
        blank=True,
        null=True
    )

    codigo_cliente = models.CharField(
        max_length=50,
        db_column='CODIGO_CLIENTE',
        blank=True,
        null=True
    )

    identificacion_fiscal = models.CharField(
        max_length=20,
        db_column='IDENTIFICACION_FISCAL',
        blank=True,
        null=True
    )

    nombre_cliente = models.CharField(
        max_length=255,
        db_column='NOMBRE_CLIENTE',
        blank=True,
        null=True
    )

    fecha_factura = models.DateField(
        db_column='FECHA_FACTURA',
        blank=True,
        null=True
    )

    fecha_vencimiento = models.DateField(
        db_column='FECHA_VENCIMIENTO',
        blank=True,
        null=True
    )

    valor_total_pagado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='VALOR_TOTAL_PAGADO',
        blank=True,
        null=True
    )

    valor_total_saldo_a_cobrar = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='VALOR_TOTAL_SALDO_A_COBRAR',
        blank=True,
        null=True
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='BALANCE',
        blank=True,
        null=True
    )

    en_estatus_no_venta_b = models.BooleanField(
        db_column='EN_ESTATUS_NO_VENTA_B',
        blank=True,
        null=True
    )

    limite_credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='LIMITE_CREDITO',
        blank=True,
        null=True
    )

    price_list = models.CharField(
        max_length=50,
        db_column='PriceList',
        blank=True,
        null=True
    )

    salesman = models.CharField(
        max_length=100,
        db_column='SALESMAN',
        blank=True,
        null=True
    )

    riesgo = models.CharField(
        max_length=50,
        db_column='RIESGO',
        blank=True,
        null=True
    )

    terminos_de_pago_alfa_num = models.CharField(
        max_length=50,
        db_column='TERMINOS_DE_PAGO_ALFA_NUM',
        blank=True,
        null=True
    )

    terminos_de_pago_dias = models.IntegerField(
        db_column='TERMINOS_DE_PAGO_DIAS',
        blank=True,
        null=True
    )

    dias_ven = models.IntegerField(
        db_column='DIAS_VEN',
        blank=True,
        null=True
    )

    categoria_mora = models.CharField(
        max_length=90,
        db_column='CATEGORIA_MORA',
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'cuentas_cobrar'
        verbose_name = 'Cuenta por cobrar'
        verbose_name_plural = "Cuentas por cobrar"
        # app_label = 'gimpromed_sql'
        app_label = 'warehouse'

    # SOLO LECTURA
    def save(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Este modelo es de solo lectura")

    def __str__(self):
        return f"{self.codigo_factura} - {self.nombre_cliente}"

    @property
    def dias_mora_real(self):
        if not self.fecha_vencimiento:
            return 0

        hoy = date.today()
        if hoy <= self.fecha_vencimiento:
            return 0

        return (hoy - self.fecha_vencimiento).days

    @property
    def esta_vencida(self):
        return self.dias_mora_real > 0
    
    @property
    def porcentaje_credito_usado(self):
        if not self.limite_credito or self.limite_credito == 0:
            return 0

        if not self.balance:
            return 0

        return round((self.balance / self.limite_credito) * 100, 2)

    @property
    def clasificacion_mora(self):
        dias = self.dias_mora_real

        if dias <= 0:
            return "Al día"
        elif dias <= 30:
            return "Mora 1-30"
        elif dias <= 60:
            return "Mora 31-60"
        elif dias <= 90:
            return "Mora 61-90"
        else:
            return "Mora > 90"

    @property
    def color_estado(self):
        dias = self.dias_mora_real

        if dias <= 0:
            return "success"
        elif dias <= 30:
            return "warning"
        elif dias <= 60:
            return "orange"
        else:
            return "danger"

    @property
    def saldo_pendiente(self):
        if not self.valor_total_saldo_a_cobrar:
            return 0
        return self.valor_total_saldo_a_cobrar

    @property
    def riesgo_crediticio(self):
        if self.porcentaje_credito_usado > 100:
            return "Sobre límite"
        if self.dias_mora_real > 60:
            return "Alto riesgo"
        if self.dias_mora_real > 30:
            return "Riesgo medio"
        return "Normal"


################################
###### TABLAS DE PRECIOS #######
################################

class Promocion(models.Model):
    ref = models.CharField(
        max_length=45, 
        primary_key=True, 
        db_column='Ref'
    )
    detalle = models.CharField(
        max_length=100, 
        db_column='Detalle', 
        blank=True, 
        null=True
    )
    marca = models.CharField(
        max_length=45, 
        db_column='Marca', 
        blank=True, 
        null=True
    )
    precio_h = models.FloatField(
        db_column='PrecioH', 
        blank=True, 
        null=True
    )
    precio_d = models.FloatField(
        db_column='PrecioD', 
        blank=True, 
        null=True
    )
    promocion = models.CharField(
        max_length=400, 
        db_column='Promocion', 
        blank=True, 
        null=True
    )

    class Meta:
        managed = False  # IMPORTANTE: no modifica la BD
        db_table = 'promociones'
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        # app_label = 'precios'
        app_label = 'warehouse'

    def __str__(self):
        return f"{self.ref} - {self.detalle}"
