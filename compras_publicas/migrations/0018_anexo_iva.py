# Generated by Django 3.2.13 on 2024-06-27 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras_publicas', '0017_anexo_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='anexo',
            name='iva',
            field=models.FloatField(blank=True, default=0.15, verbose_name='IVA'),
        ),
    ]
