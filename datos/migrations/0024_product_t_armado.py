# Generated by Django 3.2.13 on 2023-07-24 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0023_timestamp_actualization_imp_llegadas'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='t_armado',
            field=models.FloatField(blank=True, default=0.0, null=True, verbose_name='Tiempo armado'),
        ),
    ]
