"""
Network ops for Djax.  Uses the Sharrock client.
"""
from django.conf import settings
from django.template.defaultfilters import slugify
import logging
from dateutil import parser

from pax.client import AxilentConnection
from pax.content import ContentClient

log = logging.getLogger('djax')

# ============
# = Settings =
# ============
_endpoint = 'https://www.axilent.net/api'
if hasattr(settings,'AXILENT_ENDPOINT') and settings.AXILENT_ENDPOINT:
    _endpoint = settings.AXILENT_ENDPOINT

_api_version = 'beta3'
if hasattr(settings,'AXILENT_API_VERSION') and settings.AXILENT_API_VERSION:
    _api_version = settings.AXILENT_API_VERSION

if not hasattr(settings,'AXILENT_API_KEY') or not settings.AXILENT_API_KEY:
    raise ValueError('You must set the AXILENT_API_KEY in Django settings.')

_api_key = settings.AXILENT_API_KEY

# ===========
# = Clients =
# ===========
cx = AxilentConnection(_api_key,_api_version,_endpoint)

content_client = ContentClient(cx)

# =============
# = Functions =
# =============
# def is_update_available(content_type,content_key,last_updated):
#     """
#     Determines if a newer update is available for the specified content item.
#     """
#     try:
#         updated = c.latest_update(content_type,content_key)
#         if updated:
#             if updated > last_updated:
#                 return True
#             else:
#                 return False
#         else:
#             return True
#     except:
#         log.exception('Exception while checking for update availability for %s:%s' % (content_type,content_key))
#         return False
# 
# def get_update(content_type,content_key):
#     """
#     Gets the specified content item from the server.
#     """
#     try:
#         return c.get_content(content_type,content_key)
#     except:
#         log.exception('Exception while retrieving content update from Axilent for %s:%s.' % (content_type,content_key))
#         return {}
# 
# def get_content_keys(content_type):
#     """
#     Gets a list of content keys for the specified content type.
#     """
#     return c.content_keys(content_type)
