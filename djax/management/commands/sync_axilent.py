"""
Synchronizes the local model with Axilent.
"""
from django.core.management.base import BaseCommand
from optparse import make_option
from djax.content import sync_content

class Command(BaseCommand):
    """
    The command class.
    """
    option_list = BaseCommand.option_list + (
        make_option('--content-type',
                    dest='content_type',
                    default=None,
                    help='The ACE content type to sync.  If not specified then all the ACE content will by synced.'),
    )
    
    def handle(self,*args,**options):
        """
        Handler method.
        """
        print 'Syncing local models with ACE'
        content_type = options.get('content_type',None)
        result = None
        if content_type:
            result = sync_content(content_type_to_sync=content_type)
        else:
            result = sync_content()
        if result:
            print 'Content model has been synced with ACE'
        else:
            print '''Local model is sync-locked, suggesting a concurrent sync is underway.  
                     If you think this is an error, clear the lock by running "manage.py 
                     clear_content_sync_locks".'''
