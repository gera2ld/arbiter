from urllib import parse
from django.shortcuts import redirect, render
from django.conf import settings
from social.apps.django_app import views
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
        netloc = url_parts.netloc
        for allowed_host in allowed_hosts:
            allowed = netloc.endswith(allowed_host) if allowed_host.startswith('.') else allowed_host == netloc
            if allowed:
                next_uri = url_parts.geturl()
        else:
            next_uri = None
    return redirect(next_uri or '/')

def home(request):
    return render(request, 'arbiter/home.html', {
        'user': request.user,
    })