# Generated by Django 5.1.4 on 2025-01-17 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carta', '0009_alter_cartaitem_cliente'),
        ('datos', '0033_adminactualizationwarehaouse_mensaje'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartaitem',
            name='items_mba',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cartaitem',
            name='items',
            field=models.ManyToManyField(blank=True, null=True, to='datos.product', verbose_name='Productos'),
        ),
    ]
