# Generated by Django 3.2.13 on 2022-08-17 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0002_auto_20220802_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='etiquetadostock',
            name='actulizado',
            field=models.CharField(blank=True, max_length=50, verbose_name='Fecha de aculización'),
        ),
    ]
