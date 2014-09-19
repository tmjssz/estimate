# coding=utf8
# -*- coding: utf8 -*-
from django.forms import ModelForm, ValidationError, TextInput, Form, CharField, EmailField, TextInput, Textarea, HiddenInput
import django.forms as forms
from django.contrib.auth.models import User, Group
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.core.mail import EmailMultiAlternatives




class GroupForm(ModelForm):
    class Meta:
        model = Group
        exclude = ('permissions',)

    def __init__(self, **kwargs):
        super(GroupForm, self).__init__(**kwargs)

    def save(self, commit=True):
        """if self.instance.pk is None:
            if self.__user is None:
                raise TypeError("You didn't give an user argument to the constructor.")
            #self.instance.slug = slugify(self.instance.title)
            self.instance.user = self.__user
            self.instance.question = self.__question
            self.instance.challenge = self.__challenge
            self.instance.time_out = self.__time_out"""
            
        return super(GroupForm, self).save(commit)


class UserCreationFormCustom(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(UserCreationFormCustom, self).__init__(*args, **kwargs)

        for key, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or \
                isinstance(field.widget, forms.Textarea) or \
                isinstance(field.widget, forms.DateInput) or \
                isinstance(field.widget, forms.DateTimeInput) or \
                isinstance(field.widget, forms.TimeInput):
                field.widget.attrs.update({'placeholder': field.label})


class FriendInviteForm(Form):
    username = CharField(required=True, label='Dein Name', widget=TextInput(attrs={'placeholder': 'Dein Name'}))
    email = EmailField(required=True, label='E-Mail', widget=TextInput(attrs={'placeholder': 'E-Mail'}))
    message = CharField(required=True, label='Nachricht', widget=Textarea(attrs={'placeholder': 'Nachricht'}))
    
    def __init__(self, *args, **kwargs):
        self.__username = kwargs.pop('username', None)
        self.__email = kwargs.pop('email', None)
        self.__message = kwargs.pop('message', None)
        super(FriendInviteForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        data = self.cleaned_data
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        message = self.cleaned_data['message']

        template = get_template('userauth/mail-friend-invitation.html')
        context = Context({'message': message, 'email': email, 'name': username, 'host': settings.EMAIL_HTML_CONTENT_HOST, 'static_url': settings.STATIC_URL})
        content = template.render(context)
        
        subject, from_email, to = 'Einladung von ' + username + ' zu esti|mate', 'esti|mate <etamitse@gmail.com>', email
        text_content = u'Du wurdest von ' + username + u' zum Schaetzspiel estimate eingeladen. \n\n"' + message + u'"\n\n Schau doch mal vorbei: ' + settings.EMAIL_HTML_CONTENT_HOST + u'\n\n Estimate fordert dich heraus! Wie gut bist du im Schaetzen? Gib deine Schaetzungen zu spannenden, interessanten und lustigen Fragen ab. Finde heraus, wie gut du im Vergleich zu anderen Spielern bist. Beantworte zufaellige Fragen, spiele Challenges oder such dir Fragen aus der Sammlung aus. Du kannst deinen estiMATES auch selber Fragen stellen. Mach mit, Schaetzen macht Spass!'
        
        html_content = content
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        mail_admins(username+' hat '+email+' eingeladen', username+' hat einen Freund eingeladen.', html_message=content, fail_silently=True)


