from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template
from django.conf import settings
from django.contrib.auth.models import User, Group
from userauth.models import GroupInvitation
from questions.models import Score, Estimate
from userauth.forms import GroupForm
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import validate_email
from django.forms import ValidationError
from django.core.mail import EmailMultiAlternatives
import logging

logger = logging.getLogger('estimate.userauth.views')


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, **kwargs):
    """ Sends a mail to the admins, when a new User object is saved to the DB. """
    if kwargs.get('created', False):
            template = get_template('userauth/mail-user-registered.html')
            new_user = kwargs.get('instance')
            context = Context({'user': new_user, 'host': settings.EMAIL_HTML_CONTENT_HOST})
            content = template.render(context)
            mail_admins('[Neuer User] '+ new_user.username, 'Es hat sich ein neuer User namens '+new_user.username+' registriert.', html_message=content, fail_silently=True)


def register(request, template_name='userauth/register.html', next_page_name=None):
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST[u'username']
            pwd = request.POST[u'password1']
            new_user = authenticate(username=username, password=pwd)
            login(request, new_user)

            #template = get_template('userauth/mail-user-registered.html')
            #context = Context({'user': new_user, 'host': settings.EMAIL_HTML_CONTENT_HOST})
            #content = template.render(context)
            #mail_admins('[Neuer User] '+ new_user.username, 'Es hat sich ein neuer User namens '+new_user.username+' registriert.', html_message=content, fail_silently=True)

            if next_page_name is None:
                next_page = '/'
            else:
                next_page = reverse(next_page_name)
            return HttpResponseRedirect(next_page)
    else:
        form = UserCreationForm()
    return render_to_response(template_name, {'register_form': form},
        context_instance=RequestContext(request))

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST[u'name']
        if name:
            #form.save()
            name = request.POST[u'name']
            groups = Group.objects.filter(name=name)
            if groups:
                # group does already exist
                form = GroupForm()
                group = groups[0]
                return render_to_response('userauth/create_group.html', {'form': form, 'group': group}, context_instance=RequestContext(request))

            group, created = Group.objects.get_or_create(name=name)
            group.user_set.add(request.user)

            template = get_template('userauth/mail-group-created.html')
            context = Context({'user': request.user, 'group': group, 'host': settings.EMAIL_HTML_CONTENT_HOST})
            content = template.render(context)
            mail_admins('[Neue Gruppe] '+ group.name, 'Der User '+request.user.username+' hat eine neue Gruppe namens "'+group.name+'" erstellt.', html_message=content, fail_silently=True)
            
            return HttpResponseRedirect("/gruppe/"+str(group.id))
    else:
        form = GroupForm()
        return render_to_response('userauth/create_group.html', {'form': form}, context_instance=RequestContext(request))


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


    groups = Group.objects.all()
    groups_list = []

    for group in groups:
        if not request.user in group.user_set.all():
            # filter out own groups
            groups_list.append(group)

    return render_to_response('userauth/groups_list.html', {'groups': groups_list}, context_instance=RequestContext(request))    


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


def invite_friend(request):
    if request.method == 'POST':
        email = request.POST[u'email']
        message = request.POST[u'message']
        name = request.POST[u'name']

        try:
            validate_email(email)
        except ValidationError:
            return render_to_response('userauth/friend-invite.html', {'error': True, 'email': email, 'message': message, 'name': name}, context_instance=RequestContext(request))

        template = get_template('userauth/mail-friend-invitation.html')
        context = Context({'message': message, 'email': email, 'name': name, 'host': settings.EMAIL_HTML_CONTENT_HOST, 'static_url': settings.STATIC_URL})
        content = template.render(context)
        
        subject, from_email, to = 'Einladung von ' + name + ' zu esti|mate', 'esti|mate <etamitse@gmail.com>', email
        text_content = u'Du wurdest von ' + name + u' zum Schaetzspiel estimate eingeladen. \n\n"' + message + u'"\n\n Schau doch mal vorbei: ' + settings.EMAIL_HTML_CONTENT_HOST + u'\n\n Estimate fordert dich heraus! Wie gut bist du im Schaetzen? Gib deine Schaetzungen zu spannenden, interessanten und lustigen Fragen ab. Finde heraus, wie gut du im Vergleich zu anderen Spielern bist. Beantworte zufaellige Fragen, spiele Challenges oder such dir Fragen aus der Sammlung aus. Du kannst deinen estiMATES auch selber Fragen stellen. Mach mit, Schaetzen macht Spass!'
        
        html_content = content
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        mail_admins(name+' hat '+email+' eingeladen', name+' hat einen Freund eingeladen.', html_message=content, fail_silently=True)

        return render_to_response('userauth/friend-invite.html', {'email': email, 'message': message, 'name': name}, context_instance=RequestContext(request))

    return render_to_response('userauth/friend-invite.html', {}, context_instance=RequestContext(request))

