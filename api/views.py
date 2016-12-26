from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET, require_POST
from arbiter.utils import pop_code
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
    payload = pop_code(code)
    user = None
    if payload is not None:
        user = load_user(payload.get('uid'))
    if user is None:
        return JsonResponse({
            'error': 'Bad code',
        }, status_code=400)
    return JsonResponse(build_user_token(user))

@require_POST
@require_token
def renewal_view(request):
    return JsonResponse(build_user_token(request.user))