# Generated by Django 5.1.4 on 2025-07-08 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metro', '0005_alter_product_unidad'),
    ]

    operations = [
        migrations.AddField(
            model_name='tomafisica',
            name='cantidad_suministro',
            field=models.IntegerField(blank=True, default=0),
            preserve_default=False,
        ),
    ]
