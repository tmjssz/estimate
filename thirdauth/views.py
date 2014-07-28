from django.shortcuts import render_to_response
from django.template.context import RequestContext

def home(request):
   context = RequestContext(request,
                           {'user': request.user})
   return render_to_response('thirdauth/register.html',
                             context_instance=context)