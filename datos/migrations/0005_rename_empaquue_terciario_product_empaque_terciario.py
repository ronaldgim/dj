# Generated by Django 3.2.13 on 2022-11-29 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0004_auto_20221129_1451'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='empaquue_terciario',
            new_name='empaque_terciario',
        ),
    ]
