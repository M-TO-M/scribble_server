from apps.users.choices import SocialAccountTypeEnum
from apps.users.models import User


def save_auth_id(sender, instance: User, **kwargs):
    if getattr(instance, 'processed', True):
        return True

    if instance.social_type == SocialAccountTypeEnum.DEFAULT.value:
        instance.auth_id = instance.id
        instance.processed = True
        instance.save()
