# Generated by Django 3.2.13 on 2023-01-24 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0015_alter_timestamp_actulization_stockconsulta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timestamp',
            name='actulization_stockconsulta',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Actulización Stock Consulta'),
        ),
    ]
