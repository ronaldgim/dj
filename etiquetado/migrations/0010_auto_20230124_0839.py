# Generated by Django 3.2.13 on 2023-01-24 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0009_stockbodega'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockbodega',
            name='id',
        ),
        migrations.AlterField(
            model_name='stockbodega',
            name='product_id',
            field=models.CharField(blank=True, max_length=50, primary_key=True, serialize=False, verbose_name='Product id'),
        ),
    ]
