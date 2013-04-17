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
_endpoint = 'https://www.axilent.net'
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