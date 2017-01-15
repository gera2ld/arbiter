import hashlib, pickle, time, random
from urllib import parse
from django.core.cache import cache

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
