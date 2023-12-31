# Generated by Django 3.2.13 on 2023-01-20 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0008_estadopicking_bodega'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockBodega',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(blank=True, max_length=50, verbose_name='Product id')),
                ('product_name', models.CharField(blank=True, max_length=200, verbose_name='Product name')),
                ('group_code', models.CharField(blank=True, max_length=50, verbose_name='Group code')),
                ('um', models.CharField(blank=True, max_length=50, verbose_name='Presentación')),
                ('oh', models.IntegerField(blank=True, verbose_name='OH')),
                ('oh2', models.IntegerField(blank=True, verbose_name='OH2')),
                ('commited', models.IntegerField(blank=True, verbose_name='Commited')),
                ('quantity', models.IntegerField(blank=True, verbose_name='Quantity')),
                ('lote_id', models.CharField(blank=True, max_length=50, verbose_name='Lote')),
                ('fecha_elab_lote', models.DateField(blank=True, verbose_name='Fecha elaboración lote')),
                ('fecha_cadu_lote', models.DateField(blank=True, verbose_name='Fecha caducidad lote')),
                ('ware_code', models.CharField(blank=True, max_length=10, verbose_name='Bodega')),
                ('location', models.CharField(blank=True, max_length=10, verbose_name='Ubicación')),
            ],
        ),
    ]
