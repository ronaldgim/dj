# Generated by Django 3.2.13 on 2023-07-10 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0026_auto_20230706_1122'),
    ]

    operations = [
        migrations.AddField(
            model_name='arqueofisico',
            name='observaciones2',
            field=models.CharField(blank=True, max_length=100, verbose_name='Observaciones2'),
        ),
    ]
