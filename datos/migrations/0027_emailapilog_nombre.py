# Generated by Django 3.2.13 on 2024-07-24 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datos', '0026_emailapilog'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailapilog',
            name='nombre',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
