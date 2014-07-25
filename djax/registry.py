"""
Registry for Djax integrations.
"""
from django.conf import settings
import inspect
from django.db.models import Model
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
    from djax.content import ACEContent
    
    for app_path in settings.INSTALLED_APPS:
        if not ('djax' in app_path):
            try:
                #log.debug('Examining app %s' % app_path)
                app_module = get_module(app_path)
                if hasattr(app_module,'models'):
                    module = getattr(app_module,'models')
                    for name, attribute in inspect.getmembers(module):
                        # log.debug('content registry examining module member %s.' % name)
                        if inspect.isclass(attribute) and issubclass(attribute,Model) and issubclass(attribute,ACEContent):
                            # this is a content model, add to registry
                            try:
                                log.info('Adding model %s to content registry.' % name)
                                content_registry[attribute.ACE.content_type] = attribute
                            except AttributeError:
                                raise MalformedRegistry('All ACE content mappings must be defined with an "ACE" inner class with a "content_type" attribute.')
            except ImportError:
                log.warn('Cannot import %s.  Skipping.' % app_path)
