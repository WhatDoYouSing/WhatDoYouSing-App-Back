# Generated by Django 4.2.17 on 2025-02-22 14:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0004_merge_20250221_2258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notes',
            name='emotion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notes_emotion', to='notes.emotions'),
        ),
    ]
