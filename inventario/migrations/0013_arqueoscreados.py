# Generated by Django 3.2.13 on 2023-06-26 11:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0012_auto_20230623_1328'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArqueosCreados',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arqueo_id', models.IntegerField(blank=True, verbose_name='Arqueo')),
                ('arqueo_enum', models.CharField(blank=True, max_length=100, verbose_name='N° Arqueo')),
                ('bodega', models.CharField(blank=True, max_length=100, verbose_name='Bodega')),
                ('descripcion', models.TextField(max_length=50, verbose_name='Descripción')),
                ('estado', models.CharField(blank=True, max_length=100, verbose_name='Bodega')),
                ('fecha_hora', models.DateTimeField(auto_now_add=True, verbose_name='Fecha')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]
