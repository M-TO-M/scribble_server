from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework_tracking.models import APIRequestLog

from apps.users.choices import SocialAccountTypeEnum
from core.models import TimeStampModel
from core.validators import domain_allowlist, SpecificEmailDomainValidator, CategoryDictValidator


category_choices = [
  '국내소설',
  '외국소설(유럽,북미등)',
  '외국소설(아시아)',
  '경제/경영',
  '자기계발',
  '역사',
  '종교',
  '정치/사회',
  '예술/대중문화',
  '과학',
  '기술/공학',
  '컴퓨터/IT'
]


class NewUserManager(UserManager):
    use_in_migrations = True

    def _create_user(self, nickname, email, password, **extra_fields):
        if not nickname:
            raise ValueError("닉네임은 설정되어야 합니다")
        if extra_fields.get("social_type") == SocialAccountTypeEnum.DEFAULT.value and not email:
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
        default=dict,
        validators=[CategoryDictValidator(category_choices)]
    )
    social_type = models.CharField(
        max_length=20,
        choices=SocialAccountTypeEnum.choices(),
        default=SocialAccountTypeEnum.DEFAULT.value,
        verbose_name='소셜 로그인 플랫폼'
    )
    auth_id = models.CharField(
        max_length=50,
        null=False,
        unique=True,
        default="",
        verbose_name='소셜 로그인 계정 고유 아이디'
    )

    objects = NewUserManager()
    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'
        verbose_name = '사용자'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    @property
    def social_auth_id(self):
        return f"{self.social_type[0]}@{self.auth_id}"


class UserLoginLog(TimeStampModel, APIRequestLog):
    user_agent = models.CharField(
        max_length=300,
        verbose_name='http_user_agent'
    )

    class Meta:
        db_table = 'user_login_log'
        verbose_name = 'user_login_log'
        verbose_name_plural = verbose_name
        ordering = ['created_at']
        get_latest_by = ['created_at']

    def __str__(self):
        return '%s: %s' % (self.user, self.remote_addr)
