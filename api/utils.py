import datetime
from functools import wraps
import jwt
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.cache import cache

def cache_result(get_cache_key, timeout=30):
    def wrapper(handle):
        @wraps(handle)
        def wrapped(*k, **kw):
            cache_key = get_cache_key(*k, **kw)
            result = cache.get(cache_key)
            if result is None:
                result = handle(*k, **kw)
                if result is not None:
                    cache.set(cache_key, result, timeout)
            return result
        return wrapped
    return wrapper

def create_token(payload, lifetime=datetime.timedelta(hours=24)):
    payload['exp'] = datetime.datetime.utcnow() + lifetime
    return jwt.encode(payload, settings.SECRET_KEY).decode()

@cache_result(lambda uid: 'uid:%s' % uid)
def load_user(uid):
    try:
        return User.objects.get(id=uid)
    except User.DoesNotExist:
        pass

@cache_result(lambda token: 'token:%s' % token)
def load_user_from_token(token):
    try:
        jwt_payload = jwt.decode(token, settings.SECRET_KEY)
    except:
        jwt_payload = None
    uid = jwt_payload.get('uid') if jwt_payload else None
    if uid:
        return load_user(uid)

def build_user(user, add_token=False):
    extra = user.social_auth.first().extra_data
    data = {
        'uid': user.id,
        'nickname': user.first_name,
        'avatar': extra.get('avatar'),
    }
    if add_token:
        data['token'] = create_token({
            'uid': user.id,
        })
    return data

def require_token(handle):
    @wraps(handle)
    def wrapped(request, *k, **kw):
        authorization = request.META.get('HTTP_AUTHORIZATION')
        user = None
        if authorization and authorization.startswith('token '):
            user = load_user_from_token(authorization[6:])
        if user is None:
            return JsonResponse({
                'error': 'Invalid token',
            }, status=401)
        request.user = user
        return handle(request, *k, **kw)
    return wrapped
