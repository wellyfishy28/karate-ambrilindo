# Generated by Django 4.1.7 on 2023-09-11 01:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagan', '0012_alter_admintatami_id_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='score',
            name='peserta',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
