from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from arbiter.utils import pop_ticket
from .utils import require_token, load_user, build_user

@require_GET
@require_token
def user_view(request):
    return JsonResponse(build_user(request.user))

@require_GET
def token_view(request):
    ticket = request.GET.get('ticket')
    payload = pop_ticket(ticket)
    user = None
    uid = payload and payload.get('uid')
    if uid:
        user = load_user(uid)
    if user is None:
        return JsonResponse({
            'error': 'Invalid ticket',
        }, status=401)
    return JsonResponse(build_user(user, True))

@csrf_exempt
@require_POST
@require_token
def renewal_view(request):
    return JsonResponse(build_user(request.user, True))
