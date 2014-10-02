"""
Manually adds a content record to the local cache.  Used for associating local
models with ACE content items, when the local models already exist in the database.
(This is essentially a cleanup tool, not the preferred way to operate.)
"""
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from djax.models import AxilentContentRecord
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    """
    Command class.
    """
    
    def handle(self,*args,**options):
        """
        Handler method.
        """
        if not len(args) == 2:
            raise CommandError('Usage: add_content_record <content-key> <app-label>.<model>:<model-id>')
        
        content_key = args[0]
        app_label, compound_id = args[1].split('.')
        local_model, local_id = compound_id.split(':')
       
        content_type = None
        try:
            content_type = ContentType.objects.get(app_label=app_label,model=local_model)
        except ContentType.DoesNotExist:
            raise CommandError('No such local content type.')
        
        local_mod = content_type.model_class()
        if not hasattr(local_mod,'ACE'):
            raise CommandError('Local model %s is not configured to be linked to ACE.' % local_model)
        
        AxilentContentRecord.objects.create(local_content_type=content_type,
                                            local_id=local_id,
                                            axilent_content_type=local_mod.ACE.content_type,
                                            axilent_content_key=content_key)
        
        print 'ACE content record created'
