# Generated by Django 3.2.13 on 2023-11-22 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0014_auto_20231109_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='existencias',
            name='cuarentena',
            field=models.BooleanField(default=True, verbose_name='Cuarentena'),
        ),
        migrations.AddField(
            model_name='movimiento',
            name='cuarentena',
            field=models.BooleanField(default=True, verbose_name='Cuarentena'),
        ),
        migrations.AlterField(
            model_name='inventarioingresobodega',
            name='referencia',
            field=models.CharField(choices=[('Inventario Inicial', 'Inventario Inicial'), ('Ingreso Importación', 'Ingreso Importación'), ('Liberación', 'Liberación'), ('Ajuste', 'Ajuste')], max_length=50, verbose_name='Referencia'),
        ),
        migrations.AlterField(
            model_name='movimiento',
            name='referencia',
            field=models.CharField(blank=True, choices=[('Inventario Inicial', 'Inventario Inicial'), ('Ingreso Importación', 'Ingreso Importación'), ('Movimiento Interno', 'Movimiento Interno'), ('Liberación', 'Liberación'), ('Ajuste', 'Ajuste'), ('Picking', 'Picking')], max_length=20, verbose_name='Referencia del movimiento'),
        ),
    ]
