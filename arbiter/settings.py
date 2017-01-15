import os

environ = dict(os.environ)
try:
    from . import env
    for key in dir(env):
        if not key.startswith('_') and key.upper() == key:
            environ[key] = getattr(env, key)
except ImportError:
    pass

def as_dict():
    kw = {
        'cookie_secret': SECRET_KEY,
    }
    for key, value in globals().items():
        if not key.startswith('_') and key.upper() == key:
            kw[key] = value
    return kw

PYTHON_ENV = environ.get('PYTHON_ENV')
SECRET_KEY = environ['SECRET_KEY']
PORT = environ.get('PORT', 3100)
UNIX_SOCKET = environ.get('UNIX_SOCKET')
DB_ENGINE = environ.get('DB_ENGINE')

SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
    'social_core.backends.github.GithubOAuth2',
)
SOCIAL_AUTH_GITHUB_KEY = environ.get('SOCIAL_AUTH_GITHUB_KEY', '')
SOCIAL_AUTH_GITHUB_SECRET = environ.get('SOCIAL_AUTH_GITHUB_SECRET', '')
SOCIAL_AUTH_GITHUB_EXTRA_DATA = [
    ('avatar_url', 'avatar'),
]
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/logged-in'
SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS = environ.get('SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS', [])
# Disable social_auth sanitizer to use a custom one
SOCIAL_AUTH_SANITIZE_REDIRECTS = False
SOCIAL_AUTH_USER_MODEL = 'arbiter.models.User'