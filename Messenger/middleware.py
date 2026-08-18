from django.core.cache import cache
from django.utils import timezone


class LastSeenMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            self._update_last_seen(request.user)

        response = self.get_response(request)
        return response

    def _update_last_seen(self, user):
        cache_key = f"user_last_seen_{user.pk}"
        last_seen = cache.get(cache_key)

        if last_seen is None or (timezone.now() - last_seen).total_seconds() > 60:
            cache.set(
                cache_key,
                timezone.now(),
                timeout=60 * 60 * 24
            )
