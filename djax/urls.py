"""
URLs for Djax.
"""
from django.conf.urls.defaults import *

urlpatterns = patterns('djax.views',
    url(r'^sync-record/$','sync_record_view'),
)