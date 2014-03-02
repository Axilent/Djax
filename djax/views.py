"""
Views for Djax.
"""
from djax.content import sync_content, sync_record
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
            print 'auth disabled'
            return view(request,*args,**kwargs)
        else:
            if 'HTTP_AUTHORIZATION' in request.META:
                print 'auth credentials present, checking...'
                basic_flag, auth_string = request.META['HTTP_AUTHORIZATION'].split()
                token = base64.b64decode(auth_string)[:-1] # chop trailing colon
                try:
                    auth_token = AuthToken.objects.get(token=token)
                    print 'auth token found'
                    if auth_token.origin_domain:
                        print 'auth token requires origin domain',auth_token.origin_domain
                        origin_domain = request.META.get('REMOTE_HOST',None)
                        if not origin_domain == auth_token.origin_domain:
                            print 'non-matching origin domain'
                            return HttpResponse('Not Allowed',status=403)
                
                    print 'auth token is good, running target view'
                    return view(request,*args,**kwargs)
                except AuthToken.DoesNotExist:
                    print 'cannot find auth token'
                    pass
        
            print 'request is not authorized'
            return HttpResponse('Not Allowed',status=403)
    
    return wrapper

def phone_home(request,token=None):
    """
    Initiates a content sync as long as there is no existing sync lock.
    """
    sync_content(token)

@check_auth
def sync_record_view(request):
    """
    Syncs a single record.
    """
    content_type = request.GET.get('content_type',None)
    content_key = request.GET.get('content_key',None)
    if content_type and content_key:
        if sync_record(content_type,content_key):
            return HttpResponse('Created %s:%s' % (content_type,content_key),status=201)
        else:
            return HttpResponse('Updated %s:%s' % (content_type,content_key))
    else:
        return HttpResponse('Badly formed request, specify content_type and content_key in request params.',status=409)
