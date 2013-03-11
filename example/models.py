"""
Example usage of Djax.
"""
from django.db import models
from djax import AxilentContent

class Article(models.Model,AxilentContent):
    """
    A local article that syncs to an Axilent content type.
    """
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    
    class Axilent:
        content_type = 'Article'
        field_map = {'title':'title','body':'body'}
