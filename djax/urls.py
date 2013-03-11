"""
URLs for Djax.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('djax.views',
    url(r'^djax/(?P<token>[a-fA-F0-9]+)/$','phone_home'),
)