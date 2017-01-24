from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': 'data/cache',
    'cache.lock_dir': 'data/lock',
}

cache = CacheManager(**parse_cache_config_options(cache_opts))