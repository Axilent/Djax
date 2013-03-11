"""
Views for Djax.
"""
from djax.content import sync_content

def phone_home(request,token=None):
    """
    Initiates a content sync as long as there is no existing sync lock.
    """
    sync_content(token)
