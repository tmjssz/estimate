#!/usr/bin/env python
# coding: utf8

"""
####################################################################################################
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
 #                                                                                                 #
 #  USERAUTH VIEW - CONTENTS                                                                       #
 #  ========================                                                                       #
 #                                                                                                 #
 #  1. User Registration                                                                           #
 #  2. Account Settings                                                                            #
 #  3. Groups                                                                                      #
 #  4. Tell A Friend                                                                               #
 #                                                                                                 #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
####################################################################################################
"""
from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template
from django.conf import settings
from django.contrib.auth.models import User, Group
from userauth.models import GroupInvitation
from userauth.forms import UserCreationFormCustom, FriendInviteForm
from questions.models import Score, Estimate, Challenge
from userauth.forms import GroupForm, UserProfileForm
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import validate_email
from django.forms import ValidationError
import logging

logger = logging.getLogger('estimate.userauth.views')



""" 
==================================================================================================
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

 # 1 USER REGISTRATION
 ---------------------

    register                    // user register function
    register_done               // show menu page after successful user registration
    ensure_profile_exists       // send mail to admin on user registration

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
================================================================================================== 
"""

# User Registration
# ................................................................................................
def register(request, template_name='userauth/register.html', next_page_name=None):
    # read cookie
    guest_id = request.COOKIES.get('estimate_guest_id')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = request.POST[u'username']
            pwd = request.POST[u'password1']

            # check if user already answered questions as guest
            user = None
            if guest_id:
                if not guest_id == 'None':
                    users = User.objects.filter(id=guest_id)
                    if users:
                        user = users[0]

            if user:
                user.username = username
                user.set_password(pwd)
                user.save()
                logger.debug(user)
                new_user = authenticate(username=username, password=pwd)
                login(request, new_user)
            else:
                form.save()
                new_user = authenticate(username=username, password=pwd)
                login(request, new_user)

            if next_page_name is None:
                next_page = '/'
            else:
                next_page = reverse(next_page_name)

            response = HttpResponseRedirect(next_page)
            response.delete_cookie('estimate_guest_id')
            return response
    else:
        form = UserCreationFormCustom()
    return render_to_response(template_name, {'register_form': form},
        context_instance=RequestContext(request))


# View the menu page after successful User registration
# ................................................................................................
@login_required
def register_done(request):
    """
    Shows a menu
    """
    if request.user.is_active and request.user.is_superuser:
        is_admin = True
    else:
        is_admin = False

    challenges = Challenge.objects.filter(published=True)
    if len(challenges) == 0:
        challenges = None

    estimates = Estimate.objects.filter(user=request.user).exclude(estimate=None).order_by('percentage_error')
    
    score = 0
    for e in estimates:
        score += e.score

    number_estimates = len(estimates)
    
    return render_to_response('questions/menu.html', {'user': request.user, 'is_admin': is_admin, 'challenges': challenges, 'score': score, 'number_estimates': number_estimates, 'welcome': True}, context_instance=RequestContext(request))


# Send a Mail to admin for every User registration
# ................................................................................................
@receiver(post_save, sender=User)
def ensure_profile_exists(sender, **kwargs):
    """ Sends a mail to the admins, when a new User object is saved to the DB. """
    if kwargs.get('created', False):
            template = get_template('userauth/mail-user-registered.html')
            new_user = kwargs.get('instance')
            context = Context({'user': new_user, 'host': settings.EMAIL_HTML_CONTENT_HOST})
            content = template.render(context)
            mail_admins('[Neuer User] '+ new_user.username, 'Es hat sich ein neuer User namens '+new_user.username+' registriert.', html_message=content, fail_silently=True)





""" 
==================================================================================================
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

 # 2 ACCOUNT SETTINGS
 --------------------

    account_settings    // show the current user's account settings

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
================================================================================================== 
"""

@login_required
def account_settings(request):
    if request.method == "POST":
        user_form = UserProfileForm(data=request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
    pw_form = PasswordChangeForm(user=request.user)
    user_form = UserProfileForm(instance=request.user)
    return render(request, 'userauth/account-settings.html', {'pw_form': pw_form, 'user_form': user_form, 'user': request.user})





""" 
==================================================================================================
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

 # 3 GROUPS
 ----------

    group_list      // list all groups
    group_view      // show a single group

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
================================================================================================== 
"""

# List all Groups
# ................................................................................................
@login_required
def group_list(request):
    if request.method == 'POST':
        action = request.POST[u'action']
        if action == 'ignore-invite':
            group_id = request.POST[u'group']
            group = Group.objects.get(pk=group_id)
            inviter_id = request.POST[u'inviter']
            inviter = User.objects.get(pk=inviter_id)
            invite = GroupInvitation.objects.get(group=group, inviter=inviter, invitee=request.user)
            invite.delete()
        if action == 'create-group':
            name = request.POST[u'name']
            if name:
                groups = Group.objects.filter(name=name)
                if groups:
                    # group does already exist
                    form = GroupForm()
                    group = groups[0]
                    return render_to_response('userauth/groups_list.html', {'form': form, 'group': group}, context_instance=RequestContext(request))

                group, created = Group.objects.get_or_create(name=name)
                group.user_set.add(request.user)

                template = get_template('userauth/mail-group-created.html')
                context = Context({'user': request.user, 'group': group, 'host': settings.EMAIL_HTML_CONTENT_HOST})
                content = template.render(context)
                mail_admins('[Neue Gruppe] '+ group.name, 'Der User '+request.user.username+' hat eine neue Gruppe namens "'+group.name+'" erstellt.', html_message=content, fail_silently=True)
                
                return HttpResponseRedirect("/gruppe/"+str(group.id))


    groups = Group.objects.all()
    groups_list = []

    for group in groups:
        if not request.user in group.user_set.all():
            # filter out own groups
            groups_list.append(group)

    return render_to_response('userauth/groups_list.html', {'groups': groups_list}, context_instance=RequestContext(request))    


# Show a single Group
# ................................................................................................
@login_required
def group_view(request, id):
    group = get_object_or_404(Group, id=id)

    if request.method == 'POST':
        action = request.POST[u'action']
        if action == 'join':
            group.user_set.add(request.user)
            invites = GroupInvitation.objects.filter(group=group, invitee=request.user)
            for invite in invites:
                invite.delete()
        if action == 'leave':
            group.user_set.remove(request.user)
            if not group.user_set.all():
                # remove groups without members
                group.delete()
                return HttpResponseRedirect("/gruppe")
        if action == 'invite':
            username = request.POST[u'invitee']
            invitee = User.objects.get(username=username)
            in_db = GroupInvitation.objects.filter(group=group, inviter=request.user, invitee=invitee)
            if not in_db:
                invite = GroupInvitation.create(group, request.user, invitee)
                invite.save()
        if action == 'ignore-invite':
            invites = GroupInvitation.objects.filter(group=group, invitee=request.user)
            for invite in invites:
                invite.delete()
    
    scores = Score.objects.group_highscore(group)
    users = group.user_set.all()
    is_member = False
    if request.user in users:
        is_member = True

    if not is_member:
        gotten_invites = GroupInvitation.objects.filter(group=group, invitee=request.user)
    else:
        gotten_invites = None

    invites = GroupInvitation.objects.filter(group=group)
    ids_to_exclude = [i.invitee.pk for i in invites]
    invitable_users = User.objects.exclude(pk__in=ids_to_exclude)

    ids_to_exclude = [u.pk for u in users]
    invitable_users = invitable_users.exclude(pk__in=ids_to_exclude).order_by('username')

    scores_per_question = Score.objects.get_highscore_per_question_group(group)
    scores_best_question = Score.objects.get_highscore_best_question_group(group)
    best_estimates = []
    for s in scores_best_question:
        estimate = Estimate.objects.filter(user=s.user, percentage_error=s.score)
        if estimate:
            best_estimates.append(estimate[0])
        else:
            best_estimates.append(None)

    best_estimates = zip(scores_best_question, best_estimates)

    scores_best_percentage_error = Score.objects.get_highscore_best_percentage_error_group(group)

    return render_to_response('userauth/group_show.html', {'group': group, 'invitable_users': invitable_users, 'gotten_invites': gotten_invites, 'scores': scores, 'is_member': is_member, 'scores_per_question': scores_per_question, 'best_estimates': best_estimates, 'best_percentage_error': scores_best_percentage_error}, context_instance=RequestContext(request))    





""" 
==================================================================================================
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

 # 4 TELL A FRIEND
 -----------------

    invite_friend       // send mail to friend

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
================================================================================================== 
"""

def invite_friend(request):
    form = FriendInviteForm(initial={'username': request.user.username})

    if request.method == 'POST':
        email = request.POST[u'email']
        message = request.POST[u'message']
        username = request.POST[u'username']

        form = FriendInviteForm(request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('userauth/friend-invite.html', {'email': email, 'message': message, 'name': username}, context_instance=RequestContext(request))

    return render_to_response('userauth/friend-invite.html', {'form': form}, context_instance=RequestContext(request))

