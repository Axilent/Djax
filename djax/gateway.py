"""
Network ops for Djax.  Uses the Sharrock client.
"""
from sharrock.client import HttpClient, ResourceClient, ServiceException
from django.conf import settings
from django.template.defaultfilters import slugify
import logging
from dateutil import parser

log = logging.getLogger('djax')

# ============
# = Settings =
# ============
_endpoint = 'https://www.axilent.net'
if hasattr(settings,'AXILENT_ENDPOINT') and settings.AXILENT_ENDPOINT:
    _endpoint = settings.AXILENT_ENDPOINT

_api_verision = 'beta3'
if hasattr(settings,'AXILENT_API_VERSION') and settings.AXILENT_API_VERSION:
    _api_version = settings.AXILENT_API_VERSION

if not hasattr(settings,'AXILENT_API_KEY') or not settings.AXILENT_API_KEY:
    raise ValueError('You must set the AXILENT_API_KEY in Django settings.')

_api_key = settings.AXILENT_API_KEY

# ===========
# = Clients =
# ===========
content_resource = ResourceClient(_endpoint,'axilent.content',_api_version,'content',auth_user=_api_key)
content_api = HttpClient(_endpoint,'axilent.content',_api_version,auth_user=_api_key)

# =============
# = Functions =
# =============
def is_update_available(content_type,content_key,last_updated):
    """
    Determines if a newer update is available for the specified content item.
    """
    try:
        response = content_api.latest_update(content_type_slug=slugify(content_type),content_key=content_key)
        updated_string = response['updated']
        if updated_string:
            updated = parser.parse(update_string)
            if updated > last_updated:
                return True
            else:
                return False
        else:
            return True

def get_update(content_type,content_key):
    """
    Gets the specified content item from the server.
    """
    try:
        content_data = content_resource.get(content_type_slug=slugify(content_type),content_key=content_key)
        return content_data['data']
    except ServiceException:
        log.exception('Exception while retrieving content update from Axilent for %s:%s.' % (content_type,content_key))
        return {}

def get_content_keys(content_type):
    """
    Gets a list of content keys for the specified content type.
    """
    return content_api.getcontentkeys(content_type_slug=slugify(content_type))
