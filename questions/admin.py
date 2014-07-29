# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.timezone import now

from .models import Question, Estimate, Challenge, QuestionView


# =============================================================================
# QUESTION MODEL
# =============================================================================
def publish_question(modeladmin, request, queryset):
    queryset.update(published=True)
publish_question.short_description = "Ausgewählte Fragen veröffentlichen"

def unpublish_question(modeladmin, request, queryset):
    queryset.update(published=False)
unpublish_question.short_description = "Ausgewählte Fragen auf 'unveröffentlicht' setzen"

def stats_question(modeladmin, request, queryset):
    queryset.update(stats=True)
stats_question.short_description = "Ausgewählte Fragen in Statistik einbeziehen"

def no_stats_question(modeladmin, request, queryset):
    queryset.update(stats=False)
no_stats_question.short_description = "Ausgewählte Fragen nicht in Statistik einbeziehen"

def update_date_created(modeladmin, request, queryset):
    queryset.update(date_created=now())
    queryset.update(date_updated=now())
update_date_created.short_description = "Erstellungsdatum der ausgewählten Fragen neu setzen (jetzt)"

class QuestionAdmin(admin.ModelAdmin):
    def autor(self):
        html = '<a href="/admin/auth/user/'+str(self.author.id)+'/">'+str(self.author)+'</a>'
        return html
    autor.allow_tags = True
    prepopulated_fields = {'slug': ['title']}
    list_display = ('title', autor, 'published', 'stats')
    search_fields = ('title', 'author__username')
    list_filter = ['author', 'published', 'stats']
    readonly_fields = ['date_created', 'date_updated']
    actions = [publish_question, unpublish_question, stats_question, no_stats_question, update_date_created]


# =============================================================================
# ESTIMATE MODEL
# =============================================================================
def update_estimate_score(modeladmin, request, queryset):
    for e in queryset:
        e.update_score()
update_estimate_score.short_description = "Punkte der ausgewählten Schätzungen aktualisieren"

class EstimateAdmin(admin.ModelAdmin):
    def frage(self):
        html = '<a href="/admin/questions/question/'+str(self.question.id)+'/">'+str(self.question)+'</a>'
        return html
    frage.allow_tags = True
    def benutzer(self):
        html = '<a href="/admin/auth/user/'+str(self.user.id)+'/">'+str(self.user)+'</a>'
        return html
    benutzer.allow_tags = True
    def challenge(self):
        if self.challenge:
            html = '<a href="/admin/questions/challenge/'+str(self.challenge.id)+'/">'+str(self.challenge)+'</a>'
        else:
            html = '(leer)'
        return html
    challenge.allow_tags = True
    
    list_display = ('estimate', 'percentage_error', 'score', frage, benutzer, challenge)
    search_fields = ('question__title' ,'user__username')
    list_filter = ('user', 'question', 'challenge')
    actions = [update_estimate_score]
    readonly_fields = ['score', 'percentage_error']


# =============================================================================
# CHALLENGE MODEL
# =============================================================================
def publish_challenge(modeladmin, request, queryset):
    queryset.update(published=True)
publish_challenge.short_description = "Ausgewählte Challenges veröffentlichen"

def unpublish_challenge(modeladmin, request, queryset):
    queryset.update(published=False)
unpublish_challenge.short_description = "Ausgewählte Challenges auf 'unveröffentlicht' setzen"

class ChallengeAdmin(admin.ModelAdmin):
    def autor(self):
        html = '<a href="/admin/auth/user/'+str(self.author.id)+'/">'+str(self.author)+'</a>'
        return html
    autor.allow_tags = True
    prepopulated_fields = {'slug': ['title']}
    list_display = ('title', autor, 'published')
    search_fields = ('title' ,'author__username')
    list_filter = ('title', 'author')
    actions = [publish_challenge, unpublish_challenge]
    readonly_fields = ['date_created', 'date_updated']


# =============================================================================
# QUESTION VIEW MODEL
# =============================================================================
class QuestionViewAdmin(admin.ModelAdmin):
    def benutzer(self):
        html = '<a href="/admin/auth/user/'+str(self.user.id)+'/">'+str(self.user)+'</a>'
        return html
    benutzer.allow_tags = True

    def frage(self):
        html = '<a href="/admin/questions/question/'+str(self.question.id)+'/">'+str(self.question)+'</a>'
        return html
    frage.allow_tags = True

    def restzeit(self):
        time_max = 40
        time = self.time
        current_time = now()
        timediff = current_time - time
        seconds = int(timediff.total_seconds())
        time_left = max(0, time_max - seconds)
        html = '<a href="/admin/questions/questionview/'+str(self.id)+'/">'+str(time_left)+'</a>'
        return html
    restzeit.allow_tags = True

    list_display = (benutzer, frage, restzeit, 'time')
    search_fields = ('user__username', 'frage__title', 'time')
    list_filter = ('user', 'question')
    readonly_fields = ['time']



admin.site.register(Question, QuestionAdmin)
admin.site.register(Estimate, EstimateAdmin)
admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(QuestionView, QuestionViewAdmin)
