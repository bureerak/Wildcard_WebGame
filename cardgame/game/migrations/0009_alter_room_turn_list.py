# Generated by Django 5.1.1 on 2024-11-04 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_room_current_turn_alter_room_turn_list'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='turn_list',
            field=models.JSONField(default=['W', 'a', 'i', 't', 'i', 'n', 'g', '.', '.', '.']),
        ),
    ]
