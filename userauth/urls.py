from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^anmelden/$', 'login', {'template_name': 'userauth/login.html'},
        name='userauth_login'),
    url(r'^abmelden/$', 'logout', {'next_page': '/'},
        name='userauth_logout'),
    url(r'^passwort-aendern/$', 'password_change',
        {'template_name': 'userauth/password_change.html'},
        name='password_change'),
    url(r'^passwort-geaendert/$', 'password_change_done',
        {'template_name': 'userauth/password_change_done.html'},
        name='password_change_done')
)

urlpatterns += patterns('',
    url(r'^neuer-account/$', 'userauth.views.register',
        {'next_page_name': 'userauth_register_done'},
        name='userauth_register'),
    url(r'^willkommen/$',
        TemplateView.as_view(template_name='userauth/register_done.html'),
        name='userauth_register_done')
)

urlpatterns += patterns('userauth.views',
    url(r'^neue-gruppe/$', 'create_group', name='create_group')
)