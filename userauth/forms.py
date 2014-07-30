# coding=utf8
# -*- coding: utf8 -*-
from django.forms import ModelForm, ValidationError, TextInput
import django.forms as forms
from django.contrib.auth.models import User, Group
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.forms import UserCreationForm


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

    """def clean(self):
        username = self.cleaned_data['username']
        chars = set('.@$,')
        if any((c in chars) for c in username):
            raise forms.ValidationError(u'FEHLER.')
        return self.cleaned_data"""
