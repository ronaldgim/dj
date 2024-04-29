# Generated by Django 3.2.13 on 2023-01-31 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionProcesos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_proceso', models.CharField(blank=True, max_length=50, verbose_name='Código de procesos')),
                ('entidad', models.CharField(blank=True, max_length=100, verbose_name='Entidad')),
                ('mes', models.CharField(blank=True, max_length=50, verbose_name='Mes')),
                ('presupuesto_referencial', models.FloatField(blank=True, null=True, verbose_name='Presupuesto referencial')),
                ('valor_adjudicado', models.FloatField(blank=True, null=True, verbose_name='Valor adjuntidado')),
                ('insumos_participantes', models.CharField(blank=True, max_length=150, verbose_name='Insumos participantes')),
                ('resultado_proceso', models.CharField(blank=True, choices=[('GANADO', 'GANADO'), ('PERDIDO', 'PERDIDO'), ('NO CALIFICADO', 'NO CALIFICADO'), ('NO PARTICIPADO', 'NO PARTICIPADO')], max_length=50, verbose_name='Resultado del proceso')),
                ('empresa_ganadora', models.CharField(blank=True, max_length=100, verbose_name='Empresa ganadora')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
            ],
        ),
    ]
