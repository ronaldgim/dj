# Generated by Django 3.2.13 on 2023-04-18 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0021_registoguia'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registoguia',
            name='bodega',
        ),
        migrations.AlterField(
            model_name='registoguia',
            name='confirmado',
            field=models.CharField(blank=True, max_length=50, verbose_name='Confirmado por'),
        ),
    ]
