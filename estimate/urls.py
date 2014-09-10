from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'estimate.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^', include('questions.urls')),
    url(r'^', include('userauth.urls')),
    #(r'^kontakt/', include('contact_form.urls')),
    url(r'^$', 'thirdauth.views.home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('django.contrib.auth.urls', namespace='auth')),
)
