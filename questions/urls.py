from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from userauth.models import GroupInvitation

urlpatterns = patterns('questions.views',
    url(r'^$', 'menu_view', name='questions_menu'),
    url(r'^frage/$', 'questions_list_all', name='questions_question_all'),
    url(r'^frage/(?P<slug>[-\w]+)/$', 'question_view', name='questions_question_show'),
    url(r'^frage-einreichen$', 'question_create_view', name='questions_question_create'),

    url(r'^zufall$', 'question_random', name='questions_random'),
    url(r'^zufall/(?P<slug>[-\w]+)/$', 'question_view_random', name='questions_question_random'),

    url(r'^start$', 'question_start', name='questions_start'),
    url(r'^start/(?P<slug>[-\w]+)/$', 'question_view_start', name='questions_question_start'),

    url(r'^challenge/$', 'challenges_list_all', name='questions_challenge_all'),
    url(r'^challenge/(?P<slug>[-\w]+)/$', 'challenge_view', name='questions_challenge_show'),
    url(r'^challenge/(?P<challenge>[-\w]+)/(?P<question>[-\w]+)/$', 'challenge_question_view', name='questions_challenge_question_show'),
    
    url(r'^crowd-statistik$', 'statistics_crowd', name='questions_statistics_crowd'),
    url(r'^statistik/(?P<slug>[-\w]+)/$', 'question_statistics', name='questions_statistics_question'),

    url(r'^konto$', 'account_settings', name='questions_account'),
    url(r'^benutzer/(?P<user_id>[-\w]+)/$', 'statistics_user', name='questions_user'),
    url(r'^highscore$', 'question_highscore', name='questions_highscore'),
    url(r'^highscore/challenge/(?P<slug>[-\w]+)/$', 'challenge_highscore', name='questions_challenge_highscore'),

    url(r'^feedback/$', 'feedback', name='feedback')
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT+'/media')