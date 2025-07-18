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
    consignacion = models.IntegerField(blank=True, null=True, default=0)
    ubicacion    = models.CharField(max_length=30)
    
    # Auditoria
    creado       = models.DateTimeField(auto_now_add=True)
    actualizado  = models.DateTimeField(auto_now=True)
    usuario      = models.ForeignKey(User, verbose_name='User', blank=True, null=True, on_delete=models.PROTECT)
    activo       = models.BooleanField(default=True)
    
    def __str__(self):
        return f'Código GIM: {self.codigo_gim} - Código HM: {self.codigo_hm}'


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
