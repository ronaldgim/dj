# Generated by Django 3.2.13 on 2024-02-15 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0037_transferenciastatus_avance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transferenciastatus',
            name='n_transferencia',
            field=models.CharField(max_length=50, unique=True, verbose_name='Número de trasferencia'),
        ),
    ]
