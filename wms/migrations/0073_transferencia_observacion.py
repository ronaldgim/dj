# Generated by Django 5.1.4 on 2025-05-15 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0072_alter_facturaanulada_estado_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transferencia',
            name='observacion',
            field=models.TextField(blank=True),
        ),
    ]
