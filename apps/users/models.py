from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

from core.models import TimeStampModel
from utils.validators import domain_allowlist, SpecificEmailDomainValidator


class NewUserManager(UserManager):
    use_in_migrations = True

    def _create_user(self, nickname, email, password, **extra_fields):
        if not nickname:
            raise ValueError("닉네임은 설정되어야 합니다")
        if not email:
            raise ValueError("이메일은 설정되어야 합니다")
        email = self.normalize_email(email)
        user = self.model(nickname=nickname, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, nickname, email=None, password=None, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        return self._create_user(nickname, email, password, **kwargs)

    def create_superuser(self, nickname, email=None, password=None, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        return self._create_user(nickname, email, password, **kwargs)


class User(AbstractUser, TimeStampModel):
    username = None
    email = models.EmailField(
        max_length=255,
        verbose_name='이메일',
        validators=[SpecificEmailDomainValidator(allowlist=domain_allowlist)]
    )
    nickname = models.CharField(
        max_length=15,
        unique=True,
        verbose_name='닉네임'
    )
    profile_image = models.URLField(
        blank=True,
        null=True,
        verbose_name='프로필 사진'
    )
    category = models.JSONField(
        default=dict
    )

    objects = NewUserManager()
    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'user'
        verbose_name = '사용자'
        verbose_name_plural = verbose_name
        ordering = ['created_at']
