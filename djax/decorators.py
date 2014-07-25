"""
Decorators for Djax.  To be applied to views.
"""
from djax.models import ProfileRecord
from djax.content import ACEContent

def affinity_trigger(model_class,id_name):
    """
    Sends an affinity trigger for the identified model with the specified id name.
    The trigger will pull the id from the incoming argument to the view.
    """
    def func_builder(func):
        def view(request,*args,**kwargs):
            model_id = kwargs[id_name]
            model = model_class.objects.get(pk=model_id)
            profile = ProfileRecord.objects.for_user(request.user)
            
            # sanity check
            if not isinstance(model,ACEContent):
                raise ValueError('Model %s is not ACE Content.' % unicode(model))
            
            model.trigger_affinity(profile)
            
            return func(request,*args,**kwargs)
        
        return view
    
    return func_builder

def ban_trigger(model_class,id_name):
    """
    Sends a ban trigger for the model.
    """
    def func_builder(func):
        def view(request,*args,**kwargs):
            model_id = kwargs[id_name]
            model = model_class.objects.get(pk=model_id)
            profile = ProfileRecord.objects.for_user(request.user)
            
            # sanity check
            if not isinstance(model,ACEContent):
                raise ValueError('Model %s is not ACE Content.' % unicode(model))
            
            model.trigger_ban(profile)
            
            return func(request,*args,**kwargs)
        
        return view
    
    return func_builder

def ensure_profile(view):
    """
    Extracts or creates profile.  Will be passed to wrapped view as 'ace_profile'
    keyword argument.
    """
    def wrapper(request,*args,**kwargs):
        record, created = ProfileRecord.objects.for_request(request)
        response = view(request,ace_profile=record.profile,*args,**kwargs)
        if created:
            response.set_cookie('ace-profile',record.profile)
        return response
    
    return wrapper
