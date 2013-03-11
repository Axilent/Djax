"""
Registry for Djax integrations.
"""
from django.conf import settings
import inspect
from django.db.models import Model
from djax.content import AxilentContent
import logging

log = logging.getLogger('djax')

content_registry = {}

class MalformedRegistry(Exception):
    """
    Indicates the Djax registry has been corrupted.
    """

def get_module(module_name):
    """
    Imports and returns the named module.
    """
    module = __import__(module_name)
    components = module_name.split('.')
    for comp in components[1:]:
        module = getattr(module,comp)
    return module

def build_registry():
    """
    Builds the registry.
    """
    for app_path in settings.INSTALLED_APPS:
        if app_path != 'djax': # don't load yourself
            try:
                module = get_module('%s.models' % app_path)
                for name, attribute in inspect.getmembers(module):
                    if inspect.isclass(attribute) and issubclass(attribute,Model) and issubclass(attribute,AxilentContent):
                        # this is a content model, add to registry
                        try:
                            content_registry[attribute.Axilent.content_type] = attribute
                        except AttributeError:
                            raise MalformedRegistry('All Axilent content mappings must be defined with an "Axilent" inner class with a "content_type" attribute.')
            except ImportError:
                log.warn('Cannot import %s.  Skipping.' % app_path)
