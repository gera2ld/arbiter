from urllib import parse
from django.shortcuts import redirect, render
from django.conf import settings
from social_django import views
from .utils import create_ticket, sanitize_url

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
        def get_extra():
            ticket = create_ticket({
                'uid': request.user.id,
            })
            return ('ticket', ticket),
        next_uri = sanitize_url(next_uri, allowed_hosts, get_extra)
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
