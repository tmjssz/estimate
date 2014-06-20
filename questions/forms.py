# coding=utf8
# -*- coding: utf8 -*-
from django.forms import ModelForm, ValidationError
from django.utils.text import slugify
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template
from django.conf import settings


from questions.models import Estimate, Question

class EstimateForm(ModelForm):
    class Meta:
        model = Estimate
        exclude = ('user', 'question', 'date', 'score', 'time_out', 'percentage_error', 'challenge')

    def __init__(self, **kwargs):
        self.__user = kwargs.pop('user', None)
        self.__question = kwargs.pop('question', None)
        self.__challenge = kwargs.pop('challenge', None)
        self.__time_out = kwargs.pop('time_out', False)
        super(EstimateForm, self).__init__(**kwargs)

    def clean(self):
        if self.__user == self.__question.author:
            raise ValidationError(u'Abgabe von Schätzungen zu eigenen Fragen nicht möglich.')
        return self.cleaned_data

    def save(self, commit=True):
        if self.instance.pk is None:
            if self.__user is None:
                raise TypeError("You didn't give an user argument to the constructor.")
            #self.instance.slug = slugify(self.instance.title)
            self.instance.user = self.__user
            self.instance.question = self.__question
            self.instance.challenge = self.__challenge
            self.instance.time_out = self.__time_out
            
        return super(EstimateForm, self).save(commit)


class QuestionForm(ModelForm):
    class Meta:
        model = Question
        exclude = ('published', 'stats', 'author', 'slug', 'date_created', 'date_updated')
    
    def __init__(self, *args, **kwargs):
        self.__author = kwargs.pop('user', None)
        #self.__image = kwargs.pop('image', None)
        super(QuestionForm, self).__init__(*args, **kwargs)
    
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
            #self.instance.image = self.__image
            self.instance.published = False
            self.instance.stats = False

        template = get_template('questions/mail-question-created.html')
        context = Context({'question': self.instance, 'host': settings.EMAIL_HTML_CONTENT_HOST, 'media_url': settings.MEDIA_URL})
        content = template.render(context)
        mail_admins('[Neue Frage] '+self.instance.title, self.__author.username+' hat eine neue Frage eingereicht.', html_message=content, fail_silently=True)

        return super(QuestionForm, self).save(commit)

class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', )
