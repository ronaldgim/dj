# Generated by Django 3.2.25 on 2024-12-05 10:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0065_ordenempaque_archivo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0029_alter_arqueoscreados_estado'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventarioCerezos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(blank=True, max_length=50, verbose_name='Product id')),
                ('product_name', models.CharField(blank=True, max_length=200, verbose_name='Product name')),
                ('group_code', models.CharField(blank=True, max_length=50, verbose_name='Group code')),
                ('um', models.CharField(blank=True, max_length=50, verbose_name='Presentación')),
                ('estado', models.CharField(blank=True, max_length=20, verbose_name='Estado')),
                ('oh2', models.IntegerField(blank=True, verbose_name='OH2')),
                ('lote_id', models.CharField(blank=True, max_length=50, verbose_name='Lote')),
                ('fecha_elab_lote', models.DateField(blank=True, verbose_name='Fecha elaboración lote')),
                ('fecha_cadu_lote', models.DateField(blank=True, verbose_name='Fecha caducidad lote')),
                ('unidades_caja', models.IntegerField(blank=True, verbose_name='Unidades por caja')),
                ('numero_cajas', models.IntegerField(blank=True, verbose_name='Número de cajas')),
                ('unidades_sueltas', models.IntegerField(blank=True, verbose_name='Unidades sueltas')),
                ('total_unidades', models.IntegerField(blank=True, verbose_name='Total de unidades')),
                ('diferencia', models.IntegerField(blank=True, verbose_name='Diferencia')),
                ('observaciones', models.CharField(blank=True, max_length=100, verbose_name='Observaciones')),
                ('llenado', models.BooleanField(default=False, verbose_name='Llenado')),
                ('agregado', models.BooleanField(default=False, verbose_name='Añadido')),
                ('ubicacion', models.ForeignKey(blank=True, max_length=5, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventario_ubicacion', to='wms.ubicacion', verbose_name='Ubicación')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]
