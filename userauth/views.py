from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
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
            if next_page_name is None:
                next_page = '/'
            else:
                next_page = reverse(next_page_name)
            return HttpResponseRedirect(next_page)
    else:
        form = UserCreationForm()
    return render_to_response(template_name, {'register_form': form},
        context_instance=RequestContext(request))