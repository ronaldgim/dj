from django.db import models


# Choices resultado_proceso
RESULTADO = [
    ('GANADO', 'GANADO'),
    ('PERDIDO', 'PERDIDO'),
    ('NO CALIFICADO', 'NO CALIFICADO'),
    ('NO PARTICIPADO', 'NO PARTICIPADO'),
]

# Create your models here.
class EvaluacionProcesos(models.Model):

    codigo_proceso          = models.CharField(verbose_name='Código de procesos', max_length=50, blank=True)
    # Cliente desde tabla de clientes FILTRADO POR HOPITAL PUBLICO
    entidad                 = models.CharField(verbose_name='Entidad', max_length=300, blank=True)
    # SELECCIONAR FECHA
    fecha                    = models.DateField(verbose_name='Fecha', blank=True)
    presupuesto_referencial = models.FloatField(verbose_name='Presupuesto referencial', blank=True, null=True)
    valor_adjudicado        = models.FloatField(verbose_name='Valor adjuntidado', blank=True, null=True)
    # QUE DIJETE EL USUARIO
    insumos_participantes   = models.TextField(verbose_name='Insumos participantes', blank=True)
    resultado_proceso       = models.CharField(verbose_name='Resultado del proceso', max_length=50, choices=RESULTADO, blank=True)
    # QUE DIJITE USUARIO
    empresa_ganadora        = models.CharField(verbose_name='Empresa ganadora', max_length=100, blank=True)
    observaciones           = models.TextField(verbose_name='Observaciones', blank=True)

    def __str__(self):
        return self.codigo_proceso

    