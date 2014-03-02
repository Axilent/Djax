"""
Makes an auth token for remote management.
"""
from django.core.management.base import BaseCommand
from optparse import make_option
from djax.models import AuthToken

class Command(BaseCommand):
    """
    Command class.
    """
    option_list = BaseCommand.option_list + (
        make_option('--host',dest='host',default=None),
    )
    
    def handle(request,*args,**options):
        """
        Handler method.
        """
        origin_domain = options['host']
        token = AuthToken.objects.new_token(origin_domain)
        print 'created token',token
