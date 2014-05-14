from django.conf.urls import patterns, include, url

urlpatterns = patterns('questions.views',
    url(r'^$', 'menu_view', name='questions_menu'),
    url(r'^frage/$', 'questions_list_all', name='questions_question_all'),
    url(r'^frage/(?P<slug>[-\w]+)/$', 'question_view', name='questions_question_show'),
    url(r'^frage-einreichen$', 'question_create_view', name='questions_question_create'),

    url(r'^zufall$', 'question_view_random', name='questions_question_random'),

    url(r'^challenge/$', 'challenges_list_all', name='questions_challenge_all'),
    url(r'^challenge/(?P<slug>[-\w]+)/$', 'challenge_view', name='questions_challenge_show'),
    url(r'^challenge/(?P<challenge>[-\w]+)/(?P<question>[-\w]+)/$', 'challenge_question_view', name='questions_challenge_question_show'),
    
    url(r'^statistik$', 'statistics_all', name='questions_statistics_all'),
    url(r'^statistik/(?P<slug>[-\w]+)/$', 'question_statistics', name='questions_statistics_question'),

    url(r'^benutzer/(?P<username>[-\w]+)/$', 'statistics_user', name='questions_statistics_user'),
    url(r'^highscore$', 'question_highscore', name='questions_highscore'),
    url(r'^highscore/challenge/(?P<slug>[-\w]+)/$', 'challenge_highscore', name='questions_challenge_highscore'),
)