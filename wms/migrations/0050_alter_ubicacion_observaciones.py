# Generated by Django 3.2.13 on 2024-08-01 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0049_alter_ubicacion_observaciones'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ubicacion',
            name='observaciones',
            field=models.TextField(blank=True),
        ),
    ]
