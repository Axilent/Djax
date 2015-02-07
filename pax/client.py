"""
Main client setup for Pax.
"""
from sharrock.client import HttpClient, ResourceClient, ServiceException
import logging

log = logging.getLogger('axilent-pax')

class AxilentConnection(object):
    """
    A connection with Axilent.
    """
    def __init__(self,apikey,api_version='astoria',endpoint='https://www.axilent.net'):
        self.apikey = apikey
        self.version = api_version
        self.endpoint = endpoint
    
    def http_client(self,app):
        """
        Gets an HTTP client for the specified app.
        """
        return HttpClient('%s/api' % self.endpoint,app,self.version,auth_user=self.apikey)
    
    def resource_client(self,app,resource):
        """
        Gets a resource client for the specified app.
        """
        return ResourceClient('%s/api/resource' % self.endpoint,app,self.version,resource,auth_user=self.apikey)
