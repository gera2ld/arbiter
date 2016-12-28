from urllib import parse
from django.shortcuts import redirect, render
from django.conf import settings
from social_django import views
from .utils import create_code

allowed_hosts = getattr(settings, 'ALLOWED_REDIRECT_HOSTS', [])

def auth(request, backend):
    return views.auth(request, backend)

def complete(request, backend):
    next_uri = request.session.pop('next', None)
    if next_uri:
        request.session['next_uri'] = next_uri
    return views.complete(request, backend)

def logged_in(request):
    if not request.user.is_authenticated:
        return redirect('home')
    next_uri = request.session.pop('next_uri', None)
    if next_uri:
        url_parts = parse.urlparse(next_uri)
        qs = parse.parse_qsl(url_parts.query)
        code = create_code({
            'uid': request.user.id,
        })
        qs.append(('code', code))
        new_url_parts = list(url_parts)
        new_url_parts[4] = parse.urlencode(qs)
        hostname = url_parts.hostname
        for allowed_host in allowed_hosts:
            allowed = hostname.endswith(allowed_host) if allowed_host.startswith('.') else allowed_host == hostname
            if allowed:
                next_uri = parse.urlunparse(new_url_parts)
                break
        else:
            next_uri = None
    return redirect(next_uri or 'home')

def home(request):
    next_uri = request.GET.get('next')
    if next_uri:
        if request.user.is_authenticated:
            request.session['next_uri'] = next_uri
            return redirect('logged_in')
        querystring = '?' + parse.urlencode([('next', next_uri)])
    else:
        querystring = ''
    return render(request, 'arbiter/home.html', {
        'user': request.user,
        'querystring': querystring,
    })
