from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^user', views.user_view),
    url(r'^token', views.token_view),
    url(r'^renewal', views.renewal_view),
]