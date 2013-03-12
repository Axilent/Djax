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
    def handle(self,**options):
        """
        Handler method.
        """
        print 'Syncing local models with Axilent'
        result = sync_content()
        if result:
            print 'Content model has been synced with Axilent'
        else:
            print '''Local model is sync-locked, suggesting a concurrent sync is underway.  
                     If you think this is an error, clear the lock by running "manage.py 
                     clear_content_sync_locks".'''
