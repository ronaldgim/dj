# Generated by Django 5.1.4 on 2025-02-28 10:19

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0069_remove_facturaanulada_fecha_hora_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='facturaanulada',
            name='cliente',
            field=models.CharField(default=django.utils.timezone.now, max_length=100, verbose_name='Cliente'),
            preserve_default=False,
        ),
    ]
