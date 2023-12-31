# Generated by Django 3.2.13 on 2023-12-21 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0018_auto_20231221_0928'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimiento',
            name='estado_picking',
            field=models.CharField(blank=True, choices=[('En Despacho', 'En Despacho'), ('Despachado', 'Despachado')], max_length=20, verbose_name='Estado Picking'),
        ),
        migrations.AlterField(
            model_name='existencias',
            name='estado',
            field=models.CharField(blank=True, choices=[('Cuarentena', 'Cuarentena'), ('Disponible', 'Disponible')], max_length=20, verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='movimiento',
            name='estado',
            field=models.CharField(blank=True, choices=[('Cuarentena', 'Cuarentena'), ('Disponible', 'Disponible')], max_length=20, verbose_name='Estado Stock'),
        ),
    ]
