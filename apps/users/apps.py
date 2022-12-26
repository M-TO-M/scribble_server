from django.apps import AppConfig
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        from api.users.signals import save_auth_id
        from apps.users.models import User
        post_save.connect(save_auth_id, User)
