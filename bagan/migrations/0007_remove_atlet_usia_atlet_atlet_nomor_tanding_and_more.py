# Generated by Django 4.1.7 on 2023-08-22 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagan', '0006_remove_atlet_berat_badan_remove_atlet_tanggal_lahir_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='atlet',
            name='usia_atlet',
        ),
        migrations.AddField(
            model_name='atlet',
            name='nomor_tanding',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='atlet',
            name='tipe',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
