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
        name='userauth_register')
)

urlpatterns += patterns('userauth.views',
    url(r'^konto/$', 'account_settings', name='questions_account'),
    url(r'^gruppe/$', 'group_list', name='group_list'),
    url(r'^gruppe/(?P<id>[-\w]+)/$$', 'group_view', name='group_show'),
    url(r'^freund-einladen/$', 'invite_friend', name='invite_friend'), 
    url(r'^willkommen/$', 'register_done', name='userauth_register_done')
)