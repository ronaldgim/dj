# Generated by Django 3.2.13 on 2023-08-30 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0028_arqueoscreados_reservas_sinlote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arqueoscreados',
            name='estado',
            field=models.CharField(blank=True, max_length=100, verbose_name='Estado'),
        ),
    ]
