# Generated by Django 4.0.4 on 2022-06-01 10:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # ('rest_framework_tracking', '0008_alter_apirequestlog_id'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLoginLog',
            fields=[
                ('apirequestlog_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='rest_framework_tracking.apirequestlog')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_agent', models.CharField(max_length=300, verbose_name='http_user_agent')),
            ],
            options={
                'verbose_name': 'user_login_log',
                'verbose_name_plural': 'user_login_log',
                'db_table': 'user_login_log',
                'ordering': ['created_at'],
                'get_latest_by': ['created_at'],
            },
            bases=('rest_framework_tracking.apirequestlog', models.Model),
        ),
    ]
