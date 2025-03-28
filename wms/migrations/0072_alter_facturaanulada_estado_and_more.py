# Generated by Django 5.1.4 on 2025-03-17 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0071_alter_facturaanulada_n_factura'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facturaanulada',
            name='estado',
            field=models.CharField(choices=[('Anulado', 'Anulado'), ('Pendiente', 'Pendiente')], max_length=20, verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='movimiento',
            name='referencia',
            field=models.CharField(blank=True, choices=[('Inventario Inicial', 'Inventario Inicial'), ('Ingreso Importación', 'Ingreso Importación'), ('Movimiento Interno', 'Movimiento Interno'), ('Movimiento Grupal', 'Movimiento Grupal'), ('Liberación', 'Liberación'), ('Ajuste', 'Ajuste'), ('Picking', 'Picking'), ('Picking O.Empaque', 'Picking O.Empaque'), ('Reverso de picking', 'Reverso de picking'), ('Transferencia', 'Transferencia'), ('Nota de entrega', 'Nota de entrega'), ('Factura anulada', 'Factura anulada')], max_length=20, verbose_name='Referencia del movimiento'),
        ),
    ]
