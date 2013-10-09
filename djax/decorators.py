"""
Decorators for Djax.  To be applied to views.
"""
from djax.models import ProfileRecord
from djax.content import AxilentContent

def affinity_trigger(model_class,id_position):
    """
    Sends an affinity trigger for the identified model with the specified id name.
    The trigger will pull the id from the incoming argument to the view.
    """
    def func_builder(func):
        def view(request,*args,**kwargs):
            model_id = args[id_position]
            model = model_class.objects.get(pk=model_id)
            profile = ProfileRecord.objects.for_user(request.user)
            
            # sanity check
            if not isinstance(model,AxilentContent):
                raise ValueError('Model %s is not Axilent Content.' % unicode(model))
            
            model.trigger_affinity(profile)
            
            return func(request,*args,**kwargs)
        
        return view
    
    return func_builder

def ban_trigger(model_class,id_position):
    """
    Sends a ban trigger for the model.
    """
    def func_builder(func):
        def view(request,*args,**kwargs):
            model_id = args[id_position]
            model = model_class.objects.get(pk=model_id)
            profile = ProfileRecord.objects.for_user(request.user)
            
            # sanity check
            if not isinstance(model,AxilentContent):
                raise ValueError('Model %s is not Axilent Content.' % unicode(model))
            
            model.trigger_ban(profile)
            
            return func(request,*args,**kwargs)
        
        return view
    
    return func_builder
