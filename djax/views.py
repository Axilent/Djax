"""
Views for Djax.
"""
from djax.content import sync_content, sync_record, sync_library
from django.http import HttpResponse
import base64
from djax.models import AuthToken
from django.conf import settings

def check_auth(view):
    """
    Decorator to check auth token.
    """
    def wrapper(request,*args,**kwargs):
        if hasattr(settings,'DJAX_DISABLE_AUTH') and settings.DJAX_DISABLE_AUTH:
            return view(request,*args,**kwargs)
        else:
            if 'HTTP_AUTHORIZATION' in request.META:
                basic_flag, auth_string = request.META['HTTP_AUTHORIZATION'].split()
                token = base64.b64decode(auth_string)[:-1] # chop trailing colon
                try:
                    auth_token = AuthToken.objects.get(token=token)
                    if auth_token.origin_domain:
                        origin_domain = request.META.get('REMOTE_HOST',None)
                        if not origin_domain == auth_token.origin_domain:
                            return HttpResponse('Not Allowed',status=403)
                
                    return view(request,*args,**kwargs)
                except AuthToken.DoesNotExist:
                    pass
        
            return HttpResponse('Not Allowed',status=403)
    
    return wrapper

def phone_home(request,token=None):
    """
    Initiates a content sync as long as there is no existing sync lock.
    """
    sync_content(token)
    return HttpResponse('OK')

def refresh_library(request,token=None):
    """ 
    Initiates a push to the ACE library from the local content.
    """
    sync_library(token)
    return HttpResponse('OK')

@check_auth
def sync_record_view(request):
    """
    Syncs a single record.
    """
    content_type = request.GET.get('content_type',None)
    content_key = request.GET.get('content_key',None)
    if content_type and content_key:
        try:
            if sync_record(content_type,content_key):
                return HttpResponse('Created %s:%s' % (content_type,content_key),status=201)
            else:
                return HttpResponse('Updated %s:%s' % (content_type,content_key))
        except ValueError as ve:
            return HttpResponse(unicode(ve),status=409) # probably a mismatch of content types
    else:
        return HttpResponse('Badly formed request, specify content_type and content_key in request params.',status=409)
