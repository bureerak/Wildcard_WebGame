# Generated by Django 5.1.1 on 2024-11-07 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0014_room_center'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='score',
            field=models.JSONField(default=dict),
        ),
    ]
