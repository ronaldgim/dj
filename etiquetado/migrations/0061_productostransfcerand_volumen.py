# Generated by Django 5.1.4 on 2025-04-28 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0060_productostransfcerand_transfcerand'),
    ]

    operations = [
        migrations.AddField(
            model_name='productostransfcerand',
            name='volumen',
            field=models.FloatField(default=0.0),
        ),
    ]
