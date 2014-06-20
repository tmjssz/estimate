from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.core.mail import mail_admins
from django.template import Context
from django.template.loader import get_template
from django.conf import settings
import logging

logger = logging.getLogger('estimate.userauth.views')



def register(request, template_name='userauth/register.html', next_page_name=None):
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST[u'username']
            pwd = request.POST[u'password1']
            new_user = authenticate(username=username, password=pwd)
            login(request, new_user)

            template = get_template('userauth/mail-user-registered.html')
            context = Context({'user': new_user, 'host': settings.EMAIL_HTML_CONTENT_HOST})
            content = template.render(context)
            mail_admins('[Neuer User] '+ new_user.username, 'Es hat sich ein neuer User namens '+new_user.username+' registriert.', html_message=content, fail_silently=True)

            if next_page_name is None:
                next_page = '/'
            else:
                next_page = reverse(next_page_name)
            return HttpResponseRedirect(next_page)
    else:
        form = UserCreationForm()
    return render_to_response(template_name, {'register_form': form},
        context_instance=RequestContext(request))