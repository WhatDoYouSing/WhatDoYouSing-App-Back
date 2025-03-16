# Generated by Django 4.2.17 on 2025-02-23 09:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0005_alter_notes_emotion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notes',
            name='emotion',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, related_name='notes_emotion', to='notes.emotions'),
        ),
        migrations.AlterField(
            model_name='notes',
            name='link',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
