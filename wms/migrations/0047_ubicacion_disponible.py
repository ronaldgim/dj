# Generated by Django 3.2.13 on 2024-07-29 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0046_transferencia_ubicacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='ubicacion',
            name='disponible',
            field=models.BooleanField(default=True),
        ),
    ]
