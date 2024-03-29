# Generated by Django 3.2.13 on 2024-02-08 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0030_auto_20240131_0835'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotaEntrega',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_id_corp', models.CharField(max_length=50, verbose_name='Doc - GIMPR')),
                ('doc_id', models.CharField(max_length=30, verbose_name='Doc')),
                ('product_id', models.CharField(max_length=50, verbose_name='Product id')),
                ('lote_id', models.CharField(max_length=50, verbose_name='Lote id')),
                ('fecha_caducidad', models.DateField(verbose_name='Fecha de caducidad')),
                ('unidades', models.PositiveIntegerField(verbose_name='Unidades ingresadas')),
                ('fecha_hora', models.DateTimeField(auto_now_add=True, verbose_name='Fecha Hora')),
            ],
        ),
        migrations.CreateModel(
            name='LiberacionCuarentena',
            fields=[
                ('doc_id', models.CharField(max_length=255)),
                ('doc_id_corp', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('product_id_corp', models.CharField(max_length=255)),
                ('product_id', models.CharField(max_length=255)),
                ('lote_id', models.CharField(max_length=255)),
                ('ware_code', models.CharField(max_length=50)),
                ('location', models.CharField(max_length=50)),
                ('egreso_temp', models.CharField(max_length=50)),
                ('commited', models.PositiveIntegerField()),
                ('ware_code_corp', models.CharField(max_length=50)),
                ('ubicacion', models.CharField(max_length=50)),
                ('fecha_elaboracion_lote', models.DateTimeField()),
                ('fecha_caducidad', models.DateTimeField()),
                ('estado', models.PositiveIntegerField()),
            ],
            options={
                'unique_together': {('doc_id_corp', 'product_id_corp', 'lote_id')},
            },
        ),
    ]
