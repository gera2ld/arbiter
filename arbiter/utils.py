import hashlib, pickle, time, random, datetime
from urllib import parse
from functools import wraps
import jwt
from sqlalchemy.orm import joinedload
from social_tornado.models import TornadoStorage
from .models import *
from .cache import cache
from .settings import SECRET_KEY

ticket_cache = cache.get_cache('ticket', expire=30)

def cache_result(cache):
    def wrapper(handle):
        @wraps(handle)
        def wrapped(key):
            try:
                value = cache.get(key)
            except KeyError:
                value = handle(key)
                if value:
                    cache.put(key, value)
            return value
        return wrapped
    return wrapper

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
    ticket_cache.put(ticket, data)
    return ticket

def pop_ticket(ticket):
    ticket = str(ticket)
    try:
        data = ticket_cache.get(ticket)
    except KeyError:
        data = None
    else:
        ticket_cache.remove(ticket)
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

def create_token(payload, lifetime=datetime.timedelta(hours=24)):
    payload['exp'] = datetime.datetime.utcnow() + lifetime
    return jwt.encode(payload, SECRET_KEY).decode()

def load_user(uid):
    return session.query(TornadoStorage.user).options(joinedload('user')).filter_by(user_id=uid).one_or_none()

def load_user_from_token(token):
    try:
        jwt_payload = jwt.decode(token, SECRET_KEY)
    except:
        jwt_payload = None
    uid = jwt_payload.get('uid') if jwt_payload else None
    if uid:
        return load_user(uid)

def build_user(user, add_token=False):
    extra = user.extra_data
    data = {
        'uid': user.id,
        'nickname': extra.get('name'),
        'avatar': extra.get('avatar'),
    }
    if add_token:
        data['token'] = create_token({
            'uid': user.id,
        })
    return data
