from social_tornado.routes import SOCIAL_AUTH_ROUTES
from social_tornado import handlers
from tornado.web import url, RequestHandler
from .utils import require_auth, pop_ticket, build_user, load_user_from_token, load_user

class CompleteHandler(handlers.CompleteHandler):
    def _complete(self, backend):
        print(self.request.arguments)
        super()._complete(backend)

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

class MainHandler(RequestHandler):
    def get(self):
        print(self.current_user)
        self.write('hello, world')

routes = [
    (r'/', MainHandler),
    (r'/api/user', UserHandler),
    (r'/api/token', TokenHandler),
    (r'/api/renewal', TokenRenewalHandler),
]
routes.extend(SOCIAL_AUTH_ROUTES)
routes.extend([
    # url(r'/complete/(?P<backend>[^/]+)/', CompleteHandler, name='complete'),
])
