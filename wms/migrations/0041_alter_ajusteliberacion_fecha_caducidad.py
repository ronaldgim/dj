# Generated by Django 3.2.13 on 2024-03-01 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0040_auto_20240301_0908'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ajusteliberacion',
            name='fecha_caducidad',
            field=models.DateField(verbose_name='Fecha caducidad'),
        ),
    ]
