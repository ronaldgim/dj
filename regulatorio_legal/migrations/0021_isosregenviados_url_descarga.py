# Generated by Django 5.1.4 on 2025-04-07 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regulatorio_legal', '0020_facturaproforma_procesar_docs'),
    ]

    operations = [
        migrations.AddField(
            model_name='isosregenviados',
            name='url_descarga',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
