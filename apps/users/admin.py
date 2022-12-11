from django_api_admin.sites import site
from apps.users.models import User

site.unregister(User)
site.register(User)
