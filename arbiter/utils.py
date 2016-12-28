import hashlib, pickle, time
from django.core.cache import cache

def create_code(data):
    h = hashlib.md5()
    h.update(pickle.dumps(data))
    h.update(pickle.dumps(time.time()))
    code = h.hexdigest()[:16]
    cache.set('code:' + code, data, 30)
    return code

def pop_code(code):
    cache_key = 'code:' + code
    data = cache.get(cache_key)
    if data is not None:
        cache.delete(cache_key)
    return data