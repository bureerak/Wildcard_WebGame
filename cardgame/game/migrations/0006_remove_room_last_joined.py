# Generated by Django 5.1.1 on 2024-11-04 13:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_room_problem_card'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='last_joined',
        ),
    ]
