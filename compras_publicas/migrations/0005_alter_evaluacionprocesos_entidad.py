# Generated by Django 3.2.13 on 2023-02-03 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras_publicas', '0004_alter_evaluacionprocesos_insumos_participantes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluacionprocesos',
            name='entidad',
            field=models.CharField(blank=True, max_length=300, verbose_name='Entidad'),
        ),
    ]
