""" 
Middleware for Djax
"""
import re
from djax import triggers

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
        
        print 'in trigger middleware for',request.path
        for trigger in triggers.trigger_mappings:
            print 'evaluating trigger',trigger
            mo = trigger.regex.match(request.path[1:])
            if mo:
                trigger.fire(mo.groupdict(),request)
        
        return None
