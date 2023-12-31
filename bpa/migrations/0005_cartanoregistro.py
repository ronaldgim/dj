# Generated by Django 3.2.13 on 2022-11-25 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bpa', '0004_alter_registrosanitario_documento'),
    ]

    operations = [
        migrations.CreateModel(
            name='CartaNoRegistro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marca', models.CharField(blank=True, max_length=50, verbose_name='Marca')),
                ('documento', models.CharField(choices=[('Electrónico', 'Electrónico'), ('Fisíco', 'Fisíco')], default='Electrónico', max_length=50, verbose_name='Documento')),
                ('n_solicitud', models.CharField(blank=True, max_length=50, verbose_name='Número Solicitud')),
                ('producto', models.TextField(blank=True, verbose_name='Producto Denominado')),
                ('fecha_expedicion', models.DateField(blank=True, null=True, verbose_name='Fecha de expedición')),
                ('fecha_expiracion', models.DateField(blank=True, null=True, verbose_name='Fecha de expiración')),
                ('observacion', models.TextField(blank=True, verbose_name='Observaciones')),
            ],
        ),
    ]
