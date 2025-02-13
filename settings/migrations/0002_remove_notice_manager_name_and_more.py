# Generated by Django 4.2.17 on 2025-02-13 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notice',
            name='manager_name',
        ),
        migrations.RemoveField(
            model_name='notice',
            name='manager_profile',
        ),
        migrations.AddField(
            model_name='notice',
            name='manger_name',
            field=models.CharField(default='운영자', max_length=30),
        ),
        migrations.AddField(
            model_name='notice',
            name='manger_profile',
            field=models.IntegerField(default=0),
        ),
    ]
