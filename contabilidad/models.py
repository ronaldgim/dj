from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ClienteExcluido(models.Model):
    
    codigo_cliente = models.CharField(max_length=20, unique=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.codigo_cliente


class NotificacionCartera(models.Model):
    
    codigo_cliente = models.CharField(max_length=20, unique=True)
    correos        = models.TextField()
    errores        = models.TextField(blank=True)
    correo_text    = models.TextField()
    usuario        = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    usuario_auto   = models.CharField(blank=True, max_length=20)
    creado         = models.DateTimeField(auto_now_add=True)
    actualizado    = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.codigo_cliente