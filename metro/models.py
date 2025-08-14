from django.db import models
from users.models import User


# ESTADO_INVENTARIO = [
#     ('ABIERTO','ABIERTO'),
#     ('CERRADO','CERRADO'),
# ]

# ESTADO_TOMA_FISICA = [
#     ('CREADO','CREADO'),
#     ('EN PROCESO','EN PROCESO'),
#     ('EN PAUSA','EN PAUSA'),
#     ('FINALIZADO','FINALIZADO'),
# ]


TIPO_MOVIMIENTO = [
    ('Ingreso', 'Ingreso'),
    ('Egreso', 'Egreso'),
]

DESCRIPCION_MOVIMIENTO = [
    ('Saldo inicial', 'Saldo inicial'),
    ('Ajuste por acuerdo', 'Ajuste por acuerdo'),
    ('Incremento', 'Incremento'),
    ('Decremento', 'Decremento')
]

# Create your models here.
class Product(models.Model):
    
    # Inf producto
    orden      = models.IntegerField(blank=True)
    codigo_gim   = models.CharField(max_length=30, unique=True, db_index=True)
    codigo_hm    = models.CharField(max_length=30)
    nombre_gim   = models.CharField(max_length=100)
    nombre_hm    = models.CharField(max_length=100)
    marca        = models.CharField(max_length=30)
    
    # Inf logistica
    unidad       = models.CharField(max_length=10, blank=True)
    u_empaque    = models.IntegerField(blank=True, null=True, default=0)
    
    ####
    consignacion = models.IntegerField(blank=True, null=True, default=0)
    ubicacion    = models.CharField(max_length=30)
    precio_unitario = models.FloatField(blank=True, null=True, default=0)
    factor       = models.IntegerField(blank=True, null=True, default=0)
    
    # nota_entrega   = models.CharField(max_length=20, blank=True)  ### KATY LLENO --AMARILLO
    # fecha_nota     = models.DateField(blank=True, null=True)      ### KATY LLENO --AMARILLO
    
    # movimiento_mba = models.CharField(max_length=20, blank=True)  ### CARLITOS --LLENO FALSO
    # fecha_mba      = models.DateField(blank=True, null=True)      ### CARLITOS -- LENO FALSO
    # documento     = models.FileField(upload_to='metro_kardex', null=True, blank=True)
    
    # Auditoria
    creado       = models.DateTimeField(auto_now_add=True)
    actualizado  = models.DateTimeField(auto_now=True)
    usuario      = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.PROTECT)
    activo       = models.BooleanField(default=True)
    
    def __str__(self):
        return f'Código GIM: {self.codigo_gim} - Código HM: {self.codigo_hm}'
    
    # @property
    # def saldo(self, *args, **kwargs):
        
    #     try:
    #         if self.kardex_records:
    #             return self.kardex_records.order_by('-id').first().saldo
    #         return 0
    #     except:
    #         return 0
    
    @property
    def saldo(self):
        last_kardex = self.kardex_records.order_by('-id').first()
        if last_kardex and hasattr(last_kardex, 'saldo'):
            return last_kardex.saldo
        return 0
        # return self.consignacion
    
    @property
    def ultimo_movimiento_kardex(self, *args, **kwargs):
        try:
            if self.kardex_records:
                return self.kardex_records.order_by('id').last().actualizado
            return '-'
        except:
            return '-'
    
    @property
    def ultimo_usurio_kardex(self, *args, **kwargs):
        try:
            if self.kardex_records:
                return self.kardex_records.order_by('id').last().usuario
            return '-'
        except:
            return '-'
    
    @property
    def precio_unitario_hm(self, *args, **kwargs):
        
        if self.factor == 0 or self.precio_unitario ==0:
            return '$ 0.00'
        
        precio_unitario = round(self.factor * self.precio_unitario, 2)
        return f'$ {precio_unitario:.2f}'
    
    @property
    def precio_total(self, *args, **kwargs):
        if self.precio_unitario == 0 or self.saldo == 0:
            return '$ 0.00'
        precio_total = round(self.precio_unitario * self.saldo, 2)
        return f'$ {precio_total}'
    
    @property
    def alerta(self):
        # Retorna True si existe al menos un movimiento con algún campo faltante
        return any(
            not (mov.nota_entrega and mov.fecha_nota and mov.movimiento_mba and mov.fecha_mba)
            for mov in self.kardex_records.all()
        )

    # @property
    # def alerta(self):
    #     return self.kardex_records.filter(
    #         models.Q(nota_entrega__isnull=True) | models.Q(fecha_nota__isnull=True) |
    #         models.Q(movimiento_mba__isnull=True) | models.Q(fecha_mba__isnull=True) |
    #         models.Q(nota_entrega='') | models.Q(movimiento_mba='')
    #     ).exists()

class Inventario(models.Model):
    
    nombre       = models.CharField(max_length=100, blank=True)
    estado_inv   = models.CharField(max_length=50, blank=True, default='ABIERTO')
    estado_tf    = models.CharField(max_length=50, blank=True, default='CREADO')
    
    inicio_tf    = models.DateTimeField(null=True, blank=True)  
    fin_tf       = models.DateTimeField(null=True, blank=True)  
    
    creado       = models.DateTimeField(auto_now_add=True)
    actualizado  = models.DateTimeField(auto_now=True)
    usuario      = models.ForeignKey(User, related_name='inventarios_app_metro', on_delete=models.PROTECT)
    
    def __str__(self):
        return self.nombre

    def total_productos(self):
        """Retorna el número de productos contados"""
        return self.tomafisica_set.count()

    def productos_contados(self):
        """Retorna el número de productos contados"""
        return self.tomafisica_set.filter(llenado=True).count()

    def productos_pendientes(self):
        """Retorna el número de productos pendientes por contar"""
        return self.tomafisica_set.filter(llenado=False).count()
    
    def avance(self):
        """ Retorna porcentaje de avance """
        total = self.tomafisica_set.count()
        
        # Prevenir división por cero
        if total == 0:
            return 0
        
        contados = self.tomafisica_set.filter(llenado=True).count()
        avance = (contados / total) * 100
        return int(round(avance, 0))  # Convertir explícitamente a entero


    @property
    def enum(self):
        total_registros = Inventario.objects.filter(id__lte=self.id).count()
        enum = f'{total_registros:03d}'
        return enum 
    
    @property
    def diff_tiempo(self):
        """Formatea la diferencia de tiempo en formato HH:MM"""
        if self.inicio_tf and self.fin_tf:
            
            diff_tiempo = self.fin_tf - self.inicio_tf
            
            # Calcular horas y minutos totales
            total_seconds = int(diff_tiempo.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            # Formatear como HH:MM
            return f"{hours:02d}:{minutes:02d}"
        else:
            return "--:--"
    
    @property
    def usuario_tf(self):
        toma = self.tomafisica_set.exclude(usuario=None).order_by('actualizado').last()
        return toma.usuario if toma else None


class TomaFisica(models.Model):
    
    # Inventario
    orden               = models.IntegerField(blank=True)
    inventario          = models.ForeignKey(Inventario, on_delete=models.CASCADE)
    product             = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Toma física
    cantidad_estanteria = models.IntegerField(blank=True) 
    cantidad_bulto      = models.IntegerField(blank=True) 
    cantidad_suministro = models.IntegerField(blank=True) 
    cantidad_total      = models.IntegerField(blank=True, default=0)
    observaciones       = models.CharField(max_length=150, blank=True)

    # De control
    llenado             = models.BooleanField(default=False)
    agregado            = models.BooleanField(default=False)
    usuario             = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    actualizado         = models.DateTimeField(auto_now=True)
    revisado            = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Inventario: {self.product.codigo_gim} - Producto: {self.cantidad_total}"

    def save(self, *args, **kwargs):
        
        self.cantidad_estanteria = 0 if not self.cantidad_estanteria else self.cantidad_estanteria
        self.cantidad_bulto      = 0 if not self.cantidad_bulto else self.cantidad_bulto
        self.cantidad_suministro = 0 if not self.cantidad_suministro else self.cantidad_suministro
        self.cantidad_total      = self.cantidad_estanteria + self.cantidad_bulto + self.cantidad_suministro
        return super().save(*args, **kwargs)


class Kardex(models.Model):
    
    product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='kardex_records')
    tipo          = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    description   = models.CharField(max_length=20, choices=DESCRIPCION_MOVIMIENTO)
    
    nota_entrega  = models.CharField(max_length=20)
    fecha_nota    = models.DateField()
    
    movimiento_mba = models.CharField(max_length=20)
    fecha_mba     = models.DateField()
    
    cantidad      = models.IntegerField()
    
    nota_entrega   = models.CharField(max_length=20, blank=True)  ### KATY LLENO --AMARILLO
    fecha_nota     = models.DateField(blank=True, null=True)      ### KATY LLENO --AMARILLO
    
    movimiento_mba = models.CharField(max_length=20, blank=True)  ### CARLITOS --LLENO FALSO
    fecha_mba      = models.DateField(blank=True, null=True)      ### CARLITOS -- LENO FALSO
    documento     = models.FileField(upload_to='metro_kardex', null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    usuario      = models.ForeignKey(User, related_name='kardex_app_metro', on_delete=models.PROTECT)
    creado        = models.DateTimeField(auto_now_add=True)
    actualizado   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.codigo_gim
    
    @property
    def saldo(self):
        """
        Calcula el saldo acumulado de este producto hasta este movimiento.
        """
        movimientos_previos = Kardex.objects.filter(
            product=self.product,
            creado__lte=self.creado
        ).order_by('creado')

        saldo = 0        
        if self.description == 'Saldo inicial':
            return self.product.consignacion
        
        for i in movimientos_previos:
            if i.tipo == 'Ingreso':
                saldo += i.cantidad
            
            if i.tipo == 'Egreso':
                saldo -= i.cantidad
                
        return saldo
    
    
    def save(self, *args, **kwargs):
        if self.cantidad < 0:
            self.tipo  = 'Egreso'
        
        if self.cantidad > 0:
            self.tipo = 'Ingreso'
        
        super().save(*args, **kwargs)
