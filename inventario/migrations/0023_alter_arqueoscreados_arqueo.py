# Generated by Django 3.2.13 on 2023-07-06 11:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0022_remove_arqueo_productos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arqueoscreados',
            name='arqueo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='inventario.arqueo', verbose_name='Arqueo'),
        ),
    ]
