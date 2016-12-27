from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^logged-in$', views.logged_in, name='logged_in'),
    url(r'^', include(([
        url(r'^login/(?P<backend>[^/]*)/?$', views.auth, name='begin'),
        url(r'^complete/(?P<backend>[^/]*)/?$', views.complete, name='complete'),
    ], 'social'))),
    url(r'^$', views.home, name='home'),
]