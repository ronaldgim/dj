# Generated by Django 3.2.13 on 2023-10-30 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0031_etiquetadoavance'),
    ]

    operations = [
        migrations.CreateModel(
            name='EstadoEtiquetadoStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(blank=True, max_length=15, verbose_name='Código')),
                ('estado', models.CharField(blank=True, max_length=15, verbose_name='Estado')),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
