"""
URLs for Djax.
"""
try:
    from django.conf.urls.defaults import patterns, url
except ImportError:
    from django.conf.urls import patterns, url

urlpatterns = patterns('djax.views',
    url(r'^sync-record/$','sync_record_view'),
    url(r'^refresh-library/$','refresh_library'),
)