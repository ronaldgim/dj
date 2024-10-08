# Generated by Django 3.2.13 on 2024-08-30 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20230815_1600'),
        ('etiquetado', '0036_auto_20240322_1326'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnexoDoc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trasnporte', models.CharField(blank=True, max_length=20)),
                ('n_guia', models.CharField(blank=True, max_length=120)),
                ('tipo_contenido', models.CharField(blank=True, max_length=20)),
                ('contenido', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='AnexoGuia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_anexo', models.CharField(max_length=20, unique=True)),
                ('version_documento', models.CharField(default='02', max_length=3)),
                ('bodega_nombre', models.CharField(max_length=20)),
                ('bodega_codigo', models.CharField(max_length=2)),
                ('estado', models.CharField(max_length=20)),
                ('creado', models.DateField(auto_now_add=True)),
                ('contenido', models.ManyToManyField(to='etiquetado.AnexoDoc')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userperfil', verbose_name='User')),
            ],
        ),
    ]
