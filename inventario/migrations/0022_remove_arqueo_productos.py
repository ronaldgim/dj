# Generated by Django 3.2.13 on 2023-07-06 11:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0021_alter_arqueo_productos'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='arqueo',
            name='productos',
        ),
    ]
