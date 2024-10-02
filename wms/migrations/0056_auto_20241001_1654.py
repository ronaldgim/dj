# Generated by Django 3.2.25 on 2024-10-01 16:54

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0055_auto_20241001_1652'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ordenempaque',
            name='fecha_hora',
        ),
        migrations.AddField(
            model_name='ordenempaque',
            name='actualizado',
            field=models.DateTimeField(auto_now=True, verbose_name='Actualizado'),
        ),
        migrations.AddField(
            model_name='ordenempaque',
            name='creado',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Creado'),
            preserve_default=False,
        ),
    ]
