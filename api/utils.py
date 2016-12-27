import datetime, json
from functools import wraps
import jwt
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import User

def create_token(payload, lifetime=datetime.timedelta(hours=24)):
    payload['exp'] = datetime.datetime.utcnow() + lifetime
    return jwt.encode(payload, settings.SECRET_KEY)

def validate_token(token):
    try:
        return jwt.decode(token, settings.SECRET_KEY)
    except:
        pass

def load_user(uid):
    if uid:
        try:
            return User.objects.select_related('social_auth__extra_data').get(id=uid)
        except:
            pass

def build_user(user):
    return {
        'uid': user.id,
        'nickname': user.firstname,
        'extra': json.loads(user.social_auth.first().extra_data),
    }

def require_token(handle):
    @wraps(handle)
    def wrapped(request, *k, **kw):
        token = request.META.get('AUTHORIZATION')
        user = None
        jwt_payload = None
        if token.startswith('token '):
            token = token[6:]
            if token:
                jwt_payload = validate_token(token)
        if jwt_payload is not None:
            user = load_user(jwt_payload.get('uid'))
        if user is None:
            return JsonRequest({
                'error': 'Invalid token',
            }, status_code=401)
        request.user = user
        request.jwt_payload = jwt_payload
        return handle(request, *k, **kw)
    return wrapped