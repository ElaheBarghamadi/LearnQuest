from django.utils import timezone

from .services import claim_daily_login


class DailyLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.method == 'GET':
            today = timezone.localdate().isoformat()
            if request.session.get('lq_daily_login') != today:
                request.session['lq_daily_login'] = today
                claim = claim_daily_login(request.user)
                if claim.get('ok') and not claim.get('already'):
                    request.session['lq_daily_reward_toast'] = claim
        return self.get_response(request)
