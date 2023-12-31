# Generated by Django 3.2.13 on 2023-04-21 10:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20230322_0848'),
        ('etiquetado', '0024_rename_transpote_registoguia_transporte'),
    ]

    operations = [
        migrations.CreateModel(
            name='FechaEntrega',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_hora', models.DateTimeField(verbose_name='Fecha Hora de Entrega')),
                ('estado', models.CharField(max_length=30, verbose_name='Esatdo')),
                ('pedido', models.CharField(max_length=15, unique=True, verbose_name='pedido')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userperfil', verbose_name='User')),
            ],
        ),
    ]
