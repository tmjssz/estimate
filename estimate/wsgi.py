"""
WSGI config for estimate project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import sys

sys.path.insert(0, '/srv/www')
sys.path.insert(0, '/srv/www/estimate-master')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "estimate.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
