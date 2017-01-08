import hashlib, pickle, time, random
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
    cache_key = 'ticket:' + ticket
    data = cache.get(cache_key)
    if data is not None:
        cache.delete(cache_key)
    return data