# Generated by Django 3.2.13 on 2023-07-24 15:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0023_timestamp_actualization_imp_llegadas'),
        ('etiquetado', '0028_auto_20230530_1742'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductArmado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activo', models.BooleanField(default=True, verbose_name='activo')),
                ('producto', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='datos.product', verbose_name='Producto')),
            ],
        ),
    ]
