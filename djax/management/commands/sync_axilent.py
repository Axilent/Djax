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
        sync_content()
