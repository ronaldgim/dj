# Generated by Django 3.2.13 on 2023-01-24 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0013_timestamp_actulization_stockconsulta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timestamp',
            name='actulization_stockconsulta',
            field=models.DateTimeField(blank=True, verbose_name='Actulización Stock Consulta'),
        ),
    ]
