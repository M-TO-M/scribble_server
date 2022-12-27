# Generated by Django 4.1.4 on 2022-12-26 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userloginlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auth_id',
            field=models.CharField(default='', max_length=50, unique=True, verbose_name='소셜 로그인 계정 고유 아이디'),
        ),
        migrations.AddField(
            model_name='user',
            name='social_type',
            field=models.CharField(choices=[('default', 'default'), ('kakao', 'kakao')], default='default', max_length=20, verbose_name='소셜 로그인 플랫폼'),
        ),
    ]
