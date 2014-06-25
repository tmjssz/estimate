# coding=utf8
# -*- coding: utf8 -*-
from django.forms import ModelForm, ValidationError
from django.contrib.auth.models import User, Group
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template


class GroupForm(ModelForm):
    class Meta:
        model = Group
        #exclude = ('user', 'question', 'date', 'score', 'time_out', 'percentage_error', 'challenge')

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
