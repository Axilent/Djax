"""
Clears out dead sync locks.
"""
from django.core.management.base import BaseCommand
from optparse import make_option
from djax.models import ContentSyncLock

class Command(BaseCommand):
    """
    Command class.
    """
    def handle(self,**options):
        """
        Handler.
        """
        for sync_lock in ContentSyncLock.objects.all():
            sync_lock.delete()
