# Generated by Django 3.2.13 on 2024-08-22 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carta', '0008_cartaitem_autorizacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartaitem',
            name='cliente',
            field=models.CharField(max_length=150, verbose_name='Cliente'),
        ),
    ]
