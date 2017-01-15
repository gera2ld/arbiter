import hashlib, pickle, time, random, datetime
from urllib import parse
from functools import wraps
import jwt
from .models import *

def create_unique_key(*k):
    h = hashlib.md5()
    for data in k:
        h.update(pickle.dumps(data))
    h.update(pickle.dumps(time.time()))
    h.update(pickle.dumps(random.random()))
    key = h.hexdigest()[:16]
    return key

def create_ticket(data):
    ticket = create_unique_key(data)
    cache.set('ticket:' + ticket, data, 30)
    return ticket

def pop_ticket(ticket):
    cache_key = 'ticket:' + str(ticket)
    data = cache.get(cache_key)
    if data is not None:
        cache.delete(cache_key)
    return data

def sanitize_url(url, allowed_hosts, get_extra=None):
    '''
    - Prefixed dot matches all subdomains
      e.g. `.xxx.com` matches `a.xxx.com` but not `xxx.com`
    - Suffixed colon matches all ports
      e.g. `localhost:` matches `localhost` and `localhost:3000`
    '''
    url_parts = parse.urlparse(url)
    if url_parts.netloc:
        for allowed_host in allowed_hosts:
            hostname = url_parts.netloc
            if allowed_host.endswith(':'):
                hostname = hostname.split(':', 1)[0] + ':'
            allowed = hostname.endswith(allowed_host) if allowed_host.startswith('.') else allowed_host == hostname
            if allowed: break
        else:
            return
    new_url_parts = list(url_parts)
    if get_extra:
        qs = parse.parse_qsl(url_parts.query)
        qs.extend(get_extra())
        new_url_parts[4] = parse.urlencode(qs)
    return parse.urlunparse(new_url_parts)

def require_auth(handle):
    @wraps(handle)
    def wrapped(self, *k, **kw):
        if not self.current_user:
            self.set_status(401)
            self.write({
                'error': 'Invalid token',
            })
            return
        handle(self, *k, **kw)
    return wrapped

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
    return session.query(User).filter_by(id=uid).one_or_none()

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
