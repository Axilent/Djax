"""
Revokes an auth token for remote management.
"""
from django.core.management.base import BaseCommand
from optparse import make_option
from djax.models import AuthToken

class Command(BaseCommand):
    """
    Command class.
    """
    option_list = BaseCommand.option_list + (
        make_option('--token',dest='token',default=None),
    )
    
    def handle(request,*args,**options):
        """
        Handler method.
        """
        try:
            token = AuthToken.objects.get(token=options['token'])
            token.delete()
            print 'Deleted token',options['token']
        except AuthToken.DoesNotExist:
            print 'Cannot find token',options['token'],'in this Djax install.'
