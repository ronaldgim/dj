# Generated by Django 3.2.13 on 2023-04-20 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carta', '0007_cartaprocesos_autorizacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartaitem',
            name='autorizacion',
            field=models.CharField(blank=True, max_length=450, verbose_name='Autorización'),
        ),
    ]
