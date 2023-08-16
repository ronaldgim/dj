# Generated by Django 3.2.13 on 2023-01-17 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bpa', '0005_cartanoregistro'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportacionesExcel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('excel', models.FileField(upload_to='excel_importacion', verbose_name='Importación')),
                ('marca', models.CharField(max_length=150, verbose_name='Marca')),
                ('orden_importacion', models.CharField(max_length=150, verbose_name='Orden/Importación')),
            ],
        ),
    ]
