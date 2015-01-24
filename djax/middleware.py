""" 
Middleware for Djax
"""
import re
from djax.triggers import trigger_mappings

class TriggerMiddleware(object):
    """ 
    Middleware that applies triggermaps.
    """
    def process_request(self,request):
        """ 
        Processes the http request.  Will fire triggers for matching request paths.
        """
        print 'in trigger middleware for',request.path
        for trigger in trigger_mappings:
            mo = trigger.regex.match(request.path)
            if mo:
                trigger.fire(mo.groupdict(),request)
        
        return None
