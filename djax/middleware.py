""" 
Middleware for Djax
"""
import re
from djax import triggers
import logging

log = logging.getLogger('djax')

cookie_age = 60 * 60 * 24 * 365

class TriggerMiddleware(object):
    """ 
    Middleware that applies triggermaps.
    """
    def process_request(self,request):
        """ 
        Processes the http request.  Will fire triggers for matching request paths.
        """
        # Ensure trigger mappings
        if not triggers.trigger_mappings:
            triggers.build_mappings()
        
        # Get profile
        from djax.models import ProfileRecord
        pr, pr_created = ProfileRecord.objects.for_request(request)
        
        for trigger in triggers.trigger_mappings:
            mo = trigger.regex.match(request.path[1:])
            if mo:
                trigger.fire(mo.groupdict(),request,pr)
        
        if pr_created:
            request.session['axilent-profile'] = pr.profile
        
        return None
    
    def process_response(self,request,response):
        """ 
        If a profile guid is found in the session, drop a cookie.
        """
        if 'axilent-profile' in request.session:
            profile = request.session['axilent-profile']
            response.set_cookie('axilent-profile',profile,max_age=cookie_age)
            del request.session['axilent-profile']
        
        return response
