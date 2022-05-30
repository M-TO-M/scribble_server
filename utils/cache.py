from django.core.cache import caches


def cache_key_function(key, key_prefix, version):
    return key_prefix + ":" + str(key)


def get_or_set_token_cache(request, user):
    # TODO: key_timeout
    cache = caches['default']
    key = str(user.id)

    cache_ip_addr = cache.get(key)
    remote_addr = request.META.get('REMOTE_ADDR')

    if cache_ip_addr is None:
        cache.set(key, remote_addr)
        return False, "ip_does_not_exist"

    if cache_ip_addr == remote_addr:
        return True, "success"

    return False, "invalid_ip"
