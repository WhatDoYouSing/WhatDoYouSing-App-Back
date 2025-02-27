# Generated by Django 4.2.17 on 2025-02-07 14:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contexts',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Emotions',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=30)),
                ('count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Notes',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_updated', models.BooleanField(default=False)),
                ('album_art', models.CharField(max_length=200)),
                ('song_title', models.CharField(max_length=200)),
                ('artist', models.CharField(max_length=200)),
                ('lyrics', models.TextField(null=True)),
                ('link', models.CharField(max_length=200)),
                ('memo', models.TextField()),
                ('visibility', models.CharField(choices=[('public', '공개'), ('friends', '친구 공개'), ('private', '비공개')], default='public', max_length=10)),
                ('location_name', models.CharField(default='public', max_length=50, null=True)),
                ('location_address', models.TextField(default='public', null=True)),
                ('scrap_count', models.IntegerField(default=0)),
                ('archive_count', models.IntegerField(default=0)),
                ('emotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emotion', to='notes.emotions')),
                ('tag_context', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_context', to='notes.contexts')),
            ],
        ),
        migrations.CreateModel(
            name='Seasons',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Times',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Plis',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('is_updated', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comments_count', models.IntegerField(default=0)),
                ('archive_count', models.IntegerField(default=0)),
                ('visibility', models.CharField(choices=[('public', '공개'), ('friends', '친구 공개'), ('private', '비공개')], default='public', max_length=10)),
                ('tag_context', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pli_tag_context', to='notes.contexts')),
                ('tag_season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pli_tag_season', to='notes.seasons')),
                ('tag_time', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pli_tag_time', to='notes.times')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PliNotes',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('note_memo', models.TextField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='notes.notes')),
                ('plis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plis', to='notes.plis')),
            ],
        ),
        migrations.AddField(
            model_name='notes',
            name='tag_season',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_season', to='notes.seasons'),
        ),
        migrations.AddField(
            model_name='notes',
            name='tag_time',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_time', to='notes.times'),
        ),
        migrations.AddField(
            model_name='notes',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
