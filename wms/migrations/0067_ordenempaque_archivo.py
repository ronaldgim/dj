# Generated by Django 5.1.4 on 2025-02-17 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0066_remove_ordenempaque_archivo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordenempaque',
            name='archivo',
            field=models.FileField(null=True, upload_to='orden_empaque'),
        ),
    ]
