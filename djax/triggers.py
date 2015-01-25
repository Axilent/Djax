""" 
Trigger functionality for Djax.
"""
from django.conf import settings
import re
from djax.gateway import trigger_client
import logging

log = logging.getLogger('djax')

trigger_mappings = []

def get_module(module_name):
    """
    Imports and returns the named module.
    """
    module = __import__(module_name)
    components = module_name.split('.')
    for comp in components[1:]:
        module = getattr(module,comp)
    return module    

def build_mappings():
    """ 
    Builds the mappings for triggers.
    """
    log.info('Building trigger mappings...')
    for app_path in settings.INSTALLED_APPS:
        if not ('djax' in app_path):
            try:
                module = get_module('%s.triggermap' % app_path)
                log.debug('Found triggermap for %s.' % app_path)
                if hasattr(module,'triggers'):
                    trigger_list = getattr(module,'triggers')
                    import_triggers(trigger_list)
            except ImportError:
                log.warn('Cannot import %s.triggermap. Skipping' % app_path)

def import_triggers(trigger_list):
    """ 
    Imports the list of triggers.
    """
    for trigger_item in trigger_list:
        if isinstance(trigger_item,Trigger):
            log.debug('Adding trigger %s.' % unicode(trigger_item))
            trigger_mappings.append(trigger_item)
        else:
            log.warn('Skipping non trigger item %s in trigger list.' % unicode(trigger_item))

class Trigger(object):
    """ 
    A trigger object.
    """
    def __init__(self,pattern,category,action,**vars):
        self.category = category
        self.action = action
        self.vars = vars
        self.regex = re.compile(pattern)
    
    def __unicode__(self):
        return u'%s : %s' % (self.category,self.action)
    
    def __repr__(self):
        return unicode(self)
    
    def build_var_dict(self,params):
        """ 
        Builds the var dictionairy from the params.
        """
        var_dict = {}
        for key, value in self.vars.items():
            if value.startswith('$'):
                param_key = value[1:]
                var_dict[key] = params[param_key]
            else:
                var_dict[key] = value
        
        return var_dict
    
    def fire(self,params,request,profile=None):
        """ 
        Fires the param.
        """
        profile_created = False
        from djax.models import ProfileRecord
        if not profile:
            profile, profile_created = ProfileRecord.objects.for_request(request)
        if hasattr(settings,'DJAX_TRIGGER_ASYNC') and settings.DJAX_TRIGGER_ASYNC:
            from djax.tasks import trigger_async
            trigger_async.delay(self,profile.profile,self.build_var_dict(params))
        else:
            self._send_trigger(profile.profile,self.build_var_dict(params))
        
        return profile, profile_created
    
    def _send_trigger(self,profile,var_dict):
        """ 
        Sends the trigger.
        """
        trigger_client.trigger(self.category,
                               self.action,
                               profile=profile,
                               variables=var_dict,
                               environment={},
                               identity={})
        
        log.info('Fired trigger %s:%s (%s) ? %s' % (self.category,self.action,profile,unicode(var_dict)))
            
    
class AffinityTrigger(Trigger):
    """ 
    An affinity trigger.
    """
    def __init__(self,pattern,category,action,pk,model,**vars):
        super(AffinityTrigger,self).__init__(pattern,category,action,**vars)
        model_instance = model.objects.get(pk=pk)
        self.content_key = model_instance.get_axilent_content_key()
        self.content_type = model_instance.get_axilent_content_type()

# ============================
# = Public Trigger Functions =
# ============================
def trigger(pattern,category,action,**vars):
    """ 
    Creates a trigger with the specified parameters.
    """
    return Trigger(pattern,category,action,**vars)

def affinity_trigger(pattern,category,action,pk,model,**vars):
    """ 
    Creates an affinity trigger.
    """
    return AffinityTrigger(pattern,category,action,pk,model,**vars)


# ================
# = Sanity Check =
# ================
if hasattr(settings,'DJAX_TRIGGER_ASYNC') and settings.DJAX_TRIGGER_ASYNC:
    try:
        import celery
    except ImportError:
        raise Exception('You must have Celery installed in order to use DJAX_TRIGGER_ASYNC.')

