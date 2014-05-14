# coding=utf8
# -*- coding: utf8 -*-
from django.forms import ModelForm, ValidationError
from django.utils.text import slugify

from questions.models import Estimate, Question

class EstimateForm(ModelForm):
    class Meta:
        model = Estimate
        exclude = ('user', 'question', 'date', 'score', 'percentage_error', 'challenge')

    def __init__(self, **kwargs):
        self.__user = kwargs.pop('user', None)
        self.__question = kwargs.pop('question', None)
        self.__challenge = kwargs.pop('challenge', None)
        super(EstimateForm, self).__init__(**kwargs)

    def save(self, commit=True):
        if self.instance.pk is None:
            if self.__user is None:
                raise TypeError("You didn't give an user argument to the constructor.")
            #self.instance.slug = slugify(self.instance.title)
            self.instance.user = self.__user
            self.instance.question = self.__question
            self.instance.challenge = self.__challenge
        return super(EstimateForm, self).save(commit)


class QuestionForm(ModelForm):
    class Meta:
        model = Question
        exclude = ('published', 'stats', 'author', 'slug', 'date_created', 'date_updated')
    
    def __init__(self, **kwargs):
        self.__author = kwargs.pop('user', None)
        super(QuestionForm, self).__init__(**kwargs)
    
    def clean(self):
        cleaned_data = self.cleaned_data
        form_title = cleaned_data.get('title')
        title_exists = Question.objects.filter(title=form_title).exists()
        if title_exists:
            raise ValidationError(u'Es existiert bereits eine Frage mit diesem Titel. Bitte wähle einen Anderen.')
        return cleaned_data
        #super(QuestionForm, self).clean()
    
    def save(self, commit=True):
        if self.instance.pk is None:
            if self.__author is None:
                raise TypeError("You didn't give an user argument to the constructor.")
            self.instance.slug = slugify(self.instance.title)
            self.instance.author = self.__author
            self.instance.published = False
            self.instance.stats = False
        return super(QuestionForm, self).save(commit)