from django.conf.urls import patterns, include, url
from social.apps.django_app.default.models import Association, Nonce

from django.contrib import admin
admin.autodiscover()

# Unregister unsued Models
admin.site.unregister(Association)
admin.site.unregister(Nonce)


urlpatterns = patterns('',
    # Examples:
    url(r'^admin/', include(admin.site.urls)),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('django.contrib.auth.urls', namespace='auth')),
    url(r'^', include('userauth.urls')),
    url(r'^', include('questions.urls')),
)
