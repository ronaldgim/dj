# Generated by Django 3.2.13 on 2023-08-15 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20230322_0848'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permiso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permiso', models.CharField(blank=True, max_length=40, verbose_name='Permiso')),
                ('descripcion', models.CharField(blank=True, max_length=300, verbose_name='Descripción')),
            ],
        ),
        migrations.AddField(
            model_name='userperfil',
            name='permisos',
            field=models.ManyToManyField(to='users.Permiso', verbose_name='Permisos'),
        ),
    ]
