"""
Lists the registered auth tokens.
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
        host = options['host']
        tokens = AuthToken.objects.all()
        if host:
            tokens = tokens.filter(origin_domain=host)
        
        for token in tokens:
            if token.origin_domain:
                print token.token,token.origin_domain
            else:
                print token.token
