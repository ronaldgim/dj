# Generated by Django 3.2.13 on 2023-06-09 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0021_timestamp_actulization_facturas'),
    ]

    operations = [
        migrations.AddField(
            model_name='timestamp',
            name='actualization_reserva_lote',
            field=models.CharField(blank=True, max_length=50, verbose_name='Reservas lotes'),
        ),
    ]
