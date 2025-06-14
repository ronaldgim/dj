# Models
from django.db import models
from django.contrib.auth.models import User

# Slugs
from django.utils.text import slugify

# Choices
DEPARTAMENTO = [('BODEGA', 'BODEGA'), ('ADMINISTRATIVO', 'ADMINISTRATIVO'),]


class Permiso(models.Model):

    permiso = models.CharField(verbose_name='Permiso', max_length=40, blank=True)
    descripcion = models.CharField(verbose_name='Descripción', max_length=300, blank=True)

    def __str__(self):
        return self.permiso


# Create your models here.
class UserPerfil(models.Model):
    
    user           = models.OneToOneField(User, on_delete=models.CASCADE)
    departamento   = models.CharField(max_length=20, choices=DEPARTAMENTO, blank=True)
    
    slug           = models.SlugField(null=False, blank=True, unique=True)

    firma_carta    = models.CharField(verbose_name='Firma Carta', max_length=40, blank=True)
    posicion_carta = models.CharField(verbose_name='Posición Carta', max_length=40, blank=True)

    permisos       = models.ManyToManyField(Permiso, verbose_name='Permisos')
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.user.username)
        super(UserPerfil, self).save(*args, **kwargs)
        
    def __str__(self):
        return self.user.username
    
    @property
    def permiso_operaciones(self):
        return self.permisos.filter(permiso='OPERACIONES').exists() or self.user.is_superuser
    
    @property
    def permiso_bodega(self):
        return self.permisos.filter(permiso='BODEGA').exists() or self.user.is_superuser
    
    @property
    def permiso_compraspublicas(self):
        return self.permisos.filter(permiso='COMPRAS PUBLICAS').exists() or self.user.is_superuser

    @property
    def permiso_ventas(self):
        return self.permisos.filter(permiso='VENTAS').exists() or self.user.is_superuser