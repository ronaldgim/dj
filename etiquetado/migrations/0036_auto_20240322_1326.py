# Generated by Django 3.2.13 on 2024-03-22 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetado', '0035_alter_estadopicking_whatsapp'),
    ]

    operations = [
        migrations.AddField(
            model_name='estadopicking',
            name='wh_fail_number',
            field=models.BooleanField(default=False, verbose_name='Wh numero sin +593'),
        ),
        migrations.AlterField(
            model_name='estadopicking',
            name='whatsapp',
            field=models.BooleanField(default=False, verbose_name='Whatsapp'),
        ),
    ]
