import os
from urllib import parse
from tornado import template
from tornado.web import url, RequestHandler
from social_tornado.routes import SOCIAL_AUTH_ROUTES
from social_tornado import handlers
from social_tornado.utils import psa
from social_core.actions import do_complete
from social_core.utils import setting_url, setting_name
from .utils import require_auth, pop_ticket, build_user, \
        load_user_from_token, load_user, create_ticket, sanitize_url

loader = template.Loader(os.path.join(os.path.dirname(__file__), 'templates'))

class UserMixIn:
    def get_current_user(self):
        user_id = self.get_secure_cookie('user_id')
        if user_id:
            return load_user(int(user_id))

class CompleteHandler(handlers.CompleteHandler):
    @psa('complete')
    def _complete(self, backend):
        redirect_name = 'next'
        redirect_value = self.backend.strategy.session_pop(redirect_name)
        self.cookies.pop(redirect_name, None)
        if redirect_value:
            self.set_secure_cookie('next_uri', redirect_value)
        do_complete(
            self.backend,
            login=lambda backend, user, social_user: self.login_user(user),
            user=self.get_current_user()
        )

class LoggedInHandler(UserMixIn, RequestHandler):
    def get(self):
        if not self.current_user:
            self.redirect('/')
            return
        next_uri = self.get_secure_cookie('next_uri')
        if next_uri:
            next_uri = next_uri.decode()
        self.clear_cookie('next_uri')
        if next_uri:
            def get_extra():
                ticket = create_ticket({
                    'uid': self.current_user.user_id,
                })
                return ('ticket', ticket),
            allowed_hosts = self.settings.get(setting_name('ALLOWED_REDIRECT_HOSTS'))
            next_uri = sanitize_url(next_uri, allowed_hosts, get_extra)
        self.redirect(next_uri or '/')

class LogOutHandler(RequestHandler):
    def get(self):
        next_uri = self.get_argument('next', default=None)
        self.clear_cookie('user_id')
        self.redirect(next_uri or '/')

class HomeHandler(UserMixIn, RequestHandler):
    def get(self):
        next_uri = self.get_argument('next', default=None)
        if next_uri:
            if self.current_user:
                self.set_secure_cookie('next_uri', next_uri)
                self.redirect('/logged-in')
                return
            querystring = '?' + parse.urlencode([('next', next_uri)])
        else:
            querystring = ''
        extra = self.current_user.extra_data if self.current_user else None
        self.write(loader.load('home.html').generate(
            user=self.current_user,
            extra=extra,
            querystring=querystring,
        ))

class APIBaseHandler(RequestHandler):
    def get_current_user(self):
        authorization = self.request.headers.get('AUTHORIZATION')
        user = None
        if authorization and authorization.startswith('token '):
            user = load_user_from_token(authorization[6:])
        return user

class UserHandler(APIBaseHandler):
    @require_auth
    def get(self):
        self.write(build_user(self.current_user))

class TokenHandler(APIBaseHandler):
    def get(self):
        ticket = self.get_argument('ticket')
        payload = pop_ticket(ticket)
        user = None
        uid = payload and payload.get('uid')
        if uid:
            user = load_user(uid)
        if user is None:
            self.set_status(401)
            self.write({
                'error': 'Invalid ticket',
            })
            return
        self.write(build_user(user, True))

class TokenRenewalHandler(APIBaseHandler):
    @require_auth
    def post(self):
        self.write(build_user(self.current_user, True))

routes = [
    (r'/', HomeHandler),
    (r'/logged-in', LoggedInHandler),
    (r'/logout', LogOutHandler),
    (r'/api/user', UserHandler),
    (r'/api/token', TokenHandler),
    (r'/api/renewal', TokenRenewalHandler),
]
routes.extend([
    url(r'/complete/(?P<backend>[^/]+)/', CompleteHandler, name='complete'),
])
routes.extend(SOCIAL_AUTH_ROUTES)
