# Generated by Django 4.1.7 on 2023-12-21 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagan', '0015_detailbagann_perebutanjuara'),
    ]

    operations = [
        migrations.AddField(
            model_name='bagan',
            name='banyaknya_juri',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
