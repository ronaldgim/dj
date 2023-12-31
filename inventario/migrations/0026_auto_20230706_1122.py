# Generated by Django 3.2.13 on 2023-07-06 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0023_timestamp_actualization_imp_llegadas'),
        ('inventario', '0025_remove_arqueoscreados_arqueo'),
    ]

    operations = [
        migrations.AddField(
            model_name='arqueo',
            name='productos',
            field=models.ManyToManyField(blank=True, to='datos.Product', verbose_name='Productos'),
        ),
        migrations.AddField(
            model_name='arqueoscreados',
            name='arqueo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='inventario.arqueo', verbose_name='Arqueo'),
        ),
    ]
