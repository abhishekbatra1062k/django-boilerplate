# Generated by Django 3.2.15 on 2024-11-24 11:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20240609_1055'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='phone_number',
        ),
        migrations.RemoveField(
            model_name='user',
            name='phone_verified',
        ),
        migrations.DeleteModel(
            name='PhoneVerification',
        ),
    ]