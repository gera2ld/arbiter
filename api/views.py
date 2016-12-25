from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.views.decorators.http import require_GET, require_POST
from .utils import require_token, create_token, load_user, build_user

@require_GET
@require_token
def user_view(request):
    return JsonResponse(build_user(request.user))

def build_user_token(user):
    token = create_token({
        'uid': user.id,
    })
    data = build_user(user)
    data['token'] = token
    return data

@require_POST
def token_view(request):
    code = request.POST.get('code')
    payload = None
    user = None
    if code:
        cache_key = 'code:' + code
        payload = cache.get(cache_key)
        if payload is not None:
            user = load_user(payload.get('uid'))
            cache.delete(cache_key)
    if user is None:
        return JsonResponse({
            'error': 'Bad code',
        }, status_code=400)
    return JsonResponse(build_user_token(user))

@require_POST
@require_token
def renewal_view(request):
    return JsonResponse(build_user_token(request.user))