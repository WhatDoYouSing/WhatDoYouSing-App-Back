# Generated by Django 4.2.17 on 2025-03-09 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_serviceid_alter_user_auth_provider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='serviceID',
            field=models.CharField(max_length=150, unique=True, verbose_name='서비스 내 아이디'),
        ),
    ]
