# Generated by Django 5.1.4 on 2025-01-21 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0042_alter_ubicacionandagoya_bodega'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ubicacionandagoya',
            name='modulo',
            field=models.CharField(default='1', max_length=10, verbose_name='ModuloPalet'),
        ),
        migrations.AlterField(
            model_name='ubicacionandagoya',
            name='nivel',
            field=models.CharField(default='1', max_length=10, verbose_name='Nivel'),
        ),
    ]
