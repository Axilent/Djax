"""
Example usage of Djax.
"""
from django.db import models
from djax.content import ACEContent

class Article(models.Model,ACEContent):
    """
    A local article that syncs to an Axilent content type.
    """
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    
    class Axilent:
        content_type = 'Article'
        field_map = {'title':'title','body':'body'}
