# Generated by Django 3.2.13 on 2022-11-01 15:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('inventario', '0004_auto_20221101_0747'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventario',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.userperfil', verbose_name='User'),
        ),
    ]
