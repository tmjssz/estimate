from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from userauth.models import GroupInvitation

urlpatterns = patterns('questions.views',
    # menu & landing page
    url(r'^$', 'menu_view', name='questions_menu'),

    # game modes
    url(r'^zufall/$', 'question_random', name='questions_random'),
    url(r'^frage/$', 'questions_list_all', name='questions_question_all'),
    url(r'^start/$', 'question_start', name='questions_start'),
    url(r'^challenge/$', 'challenges_list_all', name='questions_challenge_all'),
    url(r'^challenge/(?P<slug>[-\w]+)/$', 'challenge_view', name='questions_challenge_show'),

    # statistics
    url(r'^statistik/$', 'statistics_crowd', name='questions_statistics_crowd'),
    url(r'^statistik/(?P<slug>[-\w]+)/$', 'statistics_question', name='questions_statistics_question'),
    url(r'^benutzer/(?P<user_id>[-\w]+)/$', 'statistics_user', name='questions_user'),

    # highscores
    url(r'^highscore/$', 'highscore_all', name='questions_highscore'),
    url(r'^highscore/challenge/(?P<slug>[-\w]+)/$', 'highscore_challenge', name='questions_highscore_challenge'),

    # other
    url(r'^frage-einreichen/$', 'question_create_view', name='questions_question_create'),
    url(r'^konto/$', 'account_settings', name='questions_account'),
    url(r'^feedback/$', 'feedback', name='questions_feedback'),

    #url(r'^start/(?P<slug>[-\w]+)/$', 'question_view_start', name='questions_question_start'),
    #url(r'^challenge/(?P<challenge>[-\w]+)/(?P<question>[-\w]+)/$', 'challenge_question_view', name='questions_challenge_question_show'),

    # show question (has to be last)
    url(r'^frage/(?P<question_slug>[-\w]+)/$', 'question_view', name='questions_question_show'),
    url(r'^(?P<mode>[-\w]+)/(?P<question_slug>[-\w]+)/$', 'question_view', name='questions_mode_question_show'),
    url(r'^(?P<mode>[-\w]+)/(?P<challenge_slug>[-\w]+)/(?P<question_slug>[-\w]+)/$', 'question_view', name='questions_mode_question_show'),
        
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT+'/media')