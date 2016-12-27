from urllib import parse
from django.shortcuts import redirect, render
from django.conf import settings
from social.apps.django_app import views
from social.utils import sanitize_redirect
from .utils import create_code

allowed_hosts = getattr(settings, 'ALLOWED_REDIRECT_HOSTS', [])

def auth(request, backend):
    return views.auth(request, backend)

def complete(request, backend):
    next_uri = request.session.pop('next', None)
    if next_uri:
        request.session.set('next_uri', next_uri)
    return views.complete(request, backend)

def logged_in(request):
    if not request.user.is_authenticated:
        return redirect('/')
    next_uri = request.session.pop('next_uri', None)
    if next_uri:
        url_parts = parse.urlparse(next_uri)
        qs = parse.parse_qsl(url_parts.query)
        code = create_code({
            'uid': request.user.id,
        })
        qs.append(('code', code))
        url_parts.query = parse.urlencode(qs)
        next_uri = sanitize_redirect(allowed_hosts, url_parts.geturl())
    return redirect(next_uri or '/')

def home(request):
    return render(request, 'arbiter/home.html', {
        'user': request.user,
    })