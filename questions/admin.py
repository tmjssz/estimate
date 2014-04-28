# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Question, Estimate, Challenge


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
    actions = [publish_question, unpublish_question, stats_question, no_stats_question]


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



admin.site.register(Question, QuestionAdmin)
admin.site.register(Estimate, EstimateAdmin)
admin.site.register(Challenge, ChallengeAdmin)