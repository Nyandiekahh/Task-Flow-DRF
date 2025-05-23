# Generated by Django 5.2 on 2025-04-09 08:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventAttendee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('tentative', 'Tentative')], default='pending', max_length=10)),
                ('response_date', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('all_day', models.BooleanField(default=False)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('event_type', models.CharField(choices=[('task', 'Task'), ('meeting', 'Meeting'), ('deadline', 'Deadline'), ('reminder', 'Reminder'), ('other', 'Other')], default='other', max_length=20)),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurrence_pattern', models.CharField(blank=True, max_length=100, null=True)),
                ('recurrence_end_date', models.DateField(blank=True, null=True)),
                ('notification_minutes_before', models.IntegerField(default=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attendees', models.ManyToManyField(blank=True, related_name='calendar_events', to=settings.AUTH_USER_MODEL)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
    ]
