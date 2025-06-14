# Generated by Django 4.2.20 on 2025-06-01 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_remove_profile_is_eligible_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_eligible',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='priority_info',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
