# Generated by Django 3.2.13 on 2023-08-18 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bpa', '0007_auto_20230120_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrosanitario',
            name='activo',
            field=models.BooleanField(default=True, verbose_name='Activo'),
        ),
    ]
