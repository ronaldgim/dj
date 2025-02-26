# Generated by Django 5.1.4 on 2025-02-26 10:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0049_alter_ubicacionandagoya_pasillo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductosPedidoTemporal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=50)),
                ('cantidad', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PedidoTemporal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente', models.CharField(max_length=100)),
                ('ruc', models.CharField(max_length=15)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'PENDIENTE'), ('CERRADO', 'CERRADO')], max_length=20)),
                ('entrega', models.DateTimeField(blank=True, null=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('productos', models.ManyToManyField(blank=True, null=True, to='etiquetado.productospedidotemporal')),
            ],
        ),
    ]
