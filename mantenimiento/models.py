# Models
from django.db import models

# Slugify
from django.template.defaultfilters import slugify

# Uuid
import uuid
 
# Models
from users.models import User
 
# Choices
BODEGA = [('Andagoya', 'Andagoya'),
          ('Cerezos', 'Cerezos')]


TIPO = [('Mantenimiento Preventivo', 'Mantenimiento Preventivo'),
        ('Mantenimiento Correctivo', 'Mantenimiento Correctivo')]

ESTADO = [('PENDIENTE', 'PENDIENTE'),
          ('REALIZADO', 'REALIZADO')]

ACTIVIDAD = [('Limpieza de Cabezal', 'Limpieza de Cabezal'),
             ('Limpieza de Filtro', 'Limpieza de Filtro')]


# MyModels
class Equipo(models.Model):
    
    nombre      = models.CharField(verbose_name='Nombre', max_length=100)
    description = models.CharField(verbose_name='Descripción', max_length=300)
    ubicacion   = models.CharField(verbose_name='Ubicación', max_length=50, choices=BODEGA)
    frecuencia  = models.CharField(verbose_name='Fecuencia de mantenimiento', max_length=200, blank=True)
    mtt_por     = models.CharField(verbose_name='Empresa que realiza el mantenimiento', max_length=200, blank=True)
    
    # Timestam
    creado      = models.DateTimeField(verbose_name='Creado', auto_now_add=True)
    
    # Slug
    slug        = models.SlugField(unique=True)
    
    
    def __str__(self):
        return self.nombre


    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)
        
        
class Suministro(models.Model):
    
    equipo      = models.ForeignKey(Equipo, on_delete=models.PROTECT, verbose_name='Equipo')
    nombre      = models.CharField(verbose_name='Nombre', max_length=100)
    description = models.CharField(verbose_name='Descripción', max_length=300, blank=True)
    cantidad    = models.IntegerField(verbose_name='Cantidad', blank=True)
    precio      = models.FloatField(verbose_name='Precio', blank=True)
    observacion = models.CharField(verbose_name='Observacion', max_length=300, blank=True)
    
    # Timestamp
    fecha       = models.DateField(verbose_name='Fecha', auto_now_add=True)
    
    # slug
    slug        = models.SlugField(unique=True)
    
    
    def __str__(self):
        return f'Equipo: {self.equipo} - Suministro: {self.nombre}'


    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)


class Estadistica(models.Model):
    
    equipo       = models.ForeignKey(Equipo, on_delete=models.PROTECT, verbose_name='Equipo')
    p_detectados = models.IntegerField(verbose_name='Productos detectados', blank=True)
    c_mens       = models.IntegerField(verbose_name='Cuenta de mensajes', blank=True)
    f_seniales   = models.IntegerField(verbose_name='Fallos de señal', blank=True)
    
    # Duration fiel input '10:10:10' -> 'hor:min:seg' se almacena en microsegundos
    h_maquina    = models.DurationField(verbose_name='Horas máquina', blank=True)
    h_chorro     = models.DurationField(verbose_name='Horas chorro', blank=True)
    
    observacion  = models.CharField(verbose_name='Observación', max_length=300, blank=True)

    # Timestamp
    fecha        = models.DateField(verbose_name='Fecha', blank=True) #, auto_now_add=True)
    
    # slug
    slug         = models.SlugField(unique=True)
    
    def __str__(self):
        return f'Equipo: {self.equipo}'


    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)

    @property
    def p_codificados(self):
        p_codificados = self.p_detectados - self.f_seniales
        return p_codificados


class Mantenimiento(models.Model):

    equipo       = models.ForeignKey(Equipo, on_delete=models.PROTECT, verbose_name='Equipo')
    tipo         = models.CharField(verbose_name='Tipo de mantenimiento', max_length=30, choices=TIPO)
    producto     = models.ForeignKey(Suministro, on_delete=models.PROTECT, verbose_name='Producto', blank=True)
    observacion  = models.CharField(verbose_name='Observación', max_length=300, blank=True)

    # Timestamp
    fecha        = models.DateField(verbose_name='Fecha', auto_now_add=True)
    
    # slug
    slug         = models.SlugField(unique=True)
    
    
    def __str__(self):
        return f'Equipo: {self.equipo}'


    def save(self, *args, **kwargs):
        self.slug = slugify(uuid.uuid4())
        return super().save(*args, **kwargs)
    
    
class MantenimientoPreventivo(models.Model):
    
    # Crear
    equipo       = models.ForeignKey(Equipo, on_delete=models.PROTECT, verbose_name='Equipo')
    responsable  = models.CharField(verbose_name='Responsable', max_length=100, blank=True)
    estado       = models.CharField(verbose_name='Estado', max_length=100, choices=ESTADO)
    programado   = models.DateField(verbose_name='Programado para')
    actividad    = models.CharField(verbose_name='Actividad', max_length=100, choices=ACTIVIDAD)
    
    # Realizar
    user         = models.ForeignKey(User, verbose_name='Realizado por', blank=True, null=True, on_delete=models.PROTECT)
    realizado    = models.DateTimeField(verbose_name='Realizado en', blank=True, null=True)
    observaciones= models.CharField(verbose_name='Observaciones', max_length=200, blank=True)
    foto         = models.ImageField(verbose_name='Foto', upload_to='mtto_preventivo/', blank=True, null=True)
    
    def __str__(self):
        return f'{self.id} | Equipo: {self.equipo}, Responsable: {self.responsable}'
    
    