# Generated by Django 3.2.13 on 2022-11-18 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carta', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartaprocesos',
            name='oficio',
            field=models.CharField(max_length=50, verbose_name='Oficio'),
        ),
        migrations.AlterField(
            model_name='cartaprocesos',
            name='ruc',
            field=models.CharField(max_length=15, verbose_name='Ruc'),
        ),
    ]
