# Generated by Django 3.2.13 on 2024-07-12 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras_publicas', '0020_auto_20240712_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='decimal_formato',
            field=models.IntegerField(blank=True, default=2, verbose_name='Formato de decimal'),
        ),
    ]
