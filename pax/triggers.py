"""
Triggers API.
"""
from pax.exceptions import PaxException

class TriggerClient(object):
    """
    Client for Triggers API.
    """
    def __init__(self,axilent_connection):
        self.api = axilent_connection.http_client('axilent.triggers')
    
    def trigger(self,category,action,profile=None,variables=None,environment={},identity={}):
        """
        Sends a trigger to Axilent.
        """
        self.api.trigger(category=category,
                         action=action,
                         profile=profile,
                         variables=variables,
                         environment=environment,
                         identity=identity)

    def profile(self):
        """
        Gets a profile to use with triggers and content channels.
        """
        return self.api.profile()
