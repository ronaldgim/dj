# Generated by Django 3.2.13 on 2023-03-20 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regulatorio_legal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentolote',
            name='o_compra',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Código'),
        ),
    ]
