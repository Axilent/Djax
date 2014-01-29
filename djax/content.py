"""
Content sync for Djax
"""
from djax.registry import content_registry, build_registry
from djax.gateway import content_client, trigger_client
import uuid
import logging
from django.db.models import Manager
from django.contrib.contenttypes.models import ContentType
from pax.util import slugify

log = logging.getLogger('djax')

class AxilentContent(object):
    """
    Mixin to provide Axilent content sync services for Django models.
    """
    def get_axilent_content_key(self):
        """
        Gets the axilent content key for this content.
        """
        from djax.models import AxilentContentRecord
        try:
            record = AxilentContentRecord.objects.get_record(self)
            return record.axilent_content_key
        except AxilentContentRecord.DoesNotExist:
            return None
        
    def get_axilent_content_type(self):
        """
        Gets the axilent content type for this content.
        """
        from djax.models import AxilentContentRecord
        try:
            record = AxilentContentRecord.objects.get_record(self)
            return record.axilent_content_type
        except AxilentContentRecord.DoesNotExist:
            return None
    
    def sync_with_axilent(self):
        """
        Synchronizes the local content with the latest from Axilent.
        """
        from djax.models import AxilentContentRecord
        # 1. Check status of content at Axilent project.  Abort if not updated later than ContentRecord.
        record = AxilentContentRecord.objects.get_record(self)
        if record.update_available():
            axilent_content = record.get_update() # 2. get the updated content from Axilent
            record.sync_content(axilent_content) # 3. write to the local model
    
    def to_content_dict(self):
        """
        Renders the local model as a content dictionary.
        """
        try:
            content_dict = {}
            for axilent_field, local_field in self.Axilent.field_map.items():
                try:
                    content_dict[axilent_field] = getattr(self,local_field)
                except AttributeError:
                    raise ValueError('The local field %s is not defined in this model.' % local_field)
            
            return content_dict
        except AttributeError:
            raise ValueError('You must define an Axilent field map to create a content dict from a local model.')
    
    def push_to_library(self):
        """
        Pushes this model to the Axilent library, assuming library integration is enabled.
        
        Returns a 2-tuple of booleans indicating 1.  If the library was updated and 2. If the
        content item was created on Axilent for the first time.
        """
        from djax.models import AxilentContentRecord
        return AxilentContentRecord.objects.push_to_library(self)
    
    def push_to_graphstack(self):
        """
        Pushes this model to the graphstack associated with the active content client.
        """
        from djax.models import AxilentContentRecord
        return AxilentContentRecord.objects.push_to_graphstack(self)
    
    def archive(self):
        """
        Archives this content on Axilent.  Archived content will be removed from the workflow,
        and will be un-deployed from any Deployment Targets where it has been deployed.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.archive()
    
    def live_delete(self):
        """
        Deletes the deployed version of the content on the active graphstack.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.live_delete()
        record.delete()
    
    def tag(self,tag_term,update_library_index=True):
        """
        Tags this content.  If update_library_index is set to false then the
        tagging will not update the library search index for the content item.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.tag(tag_term,update_library_index=update_library_index)
    
    def detag(self,tag_term):
        """
        Disassociates the content from the specified tag term.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.detag(tag_term)
    
    def live_tag(self,tag_term):
        """
        Tags the deployed version of the content.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.live_tag(tag_term)
    
    def live_detag(self,tag_term):
        """
        De-tags the deployed version of the content.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.live_detag(tag_term)
    
    def reindex_search(self):
        """
        Re-indexes the deployed version of the content for search.
        """
        from djax.models import AxilentContentRecord
        record = AxilentContentRecord.objects.get_record(self)
        record.reindex()
    
    def trigger_affinity(self,profile,environment={},identity={}):
        """
        Sends affinity trigger for this content.
        """
        trigger_client.trigger('affinity',
                               slugify(self.Axilent.content_type),
                               profile=profile,
                               variables={'key':self.get_axilent_content_key()},
                               environment=environment,
                               identity=identity)
    
    def trigger_ban(self,profile,environment={},identity={}):
        """
        Sends a ban trigger for this content.
        """
        trigger_client.trigger('ban',
                               slugify(self.Axilent.content_type),
                               profile=profile,
                               variables={'key':self.get_axilent_content_key()},
                               environment=environment,
                               identity=identity)

# ======================
# = Content Operations =
# ======================

def sync_content_type(content_type):
    """
    Syncs a specific content type.
    """
    from djax.models import AxilentContentRecord
    
    content_keys = content_client.content_keys(content_type)
    for content_key in content_keys:
        try:
            record = AxilentContentRecord.objects.get(axilent_content_type=content_type,
                                                      axilent_content_key=content_key)
            axilent_content = record.get_update()
            if axilent_content:
                log.debug('Syncing local model with updated content %s.' % unicode(axilent_content))
                record.sync_content(axilent_content)
        except AxilentContentRecord.DoesNotExist:
            AxilentContentRecord.objects.create_model(content_type,content_key)

def sync_content(token=None,content_type_to_sync=None):
    """
    Synchronizes the local models with Axilent content.
    """
    from djax.models import ContentSyncLock
    
    if ContentSyncLock.objects.all().exists():
        return False # already sync locked
    
    if not token:
        token = uuid.uuid4().hex
    
    lock = ContentSyncLock.objects.create(token=token)
    
    # ensure content registry loaded
    build_registry()
    
    if content_type_to_sync:
        log.info('Syncing %s.' % content_type_to_sync)
        try:
            content_type = content_registry[content_type_to_sync]
            sync_content_type(content_type_to_sync)
        except KeyError:
            log.error('%s is not in the content registry.' % content_type_to_sync)
    else:
        for content_type in content_registry.keys():
            sync_content_type(content_type)
    
    lock.delete()
    return True # sync occured

# ===================
# = Content Channel =
# ===================
class ContentChannel(object):
    """
    Accesses an ACE content channel.
    """
    def __init__(self,name=None,flavor=None,limit=0):
        self.name = name
        self.flavor = flavor
        self.limit = limit
        self.api = content_client
    
    def _build_params(self,**params):
        p = {}                
        if 'profile' in params:
            p['profile'] = params['profile']
        
        if 'basekey' in params:
            p['basekey'] = params['basekey']
        
        if 'flavor' in params or self.flavor:
            p['flavor'] = params['flavor'] if 'flavor' in params else self.flavor
        
        if 'limit' in params or self.limit:
            p['limit'] = params['limit'] if 'limit' in params else self.limit
        
        return p
    
    def get_content(self,queryset,channel=None,profile=None,basekey=None,flavor=None,limit=0):
        """
        Gets content.  Flavor and limit params will override the defaults.
        Extracts relevant content from the supplied queryset.
        """
        from djax.models import AxilentContentRecord
        
        ctype = ContentType.objects.get_for_model(queryset.model)
        params = self._build_params(profile=profile,basekey=basekey,flavor=flavor,limit=limit)
        
        if not channel and not self.name:
            raise ValueError('Content Channel unspecified.  You must either specify the channel in the call or the constructor.')
        
        channel_slug = slugify(channel or self.channel)
        
        axl_content_type = queryset.model.Axilent.content_type
        
        results = self.api.channel(channel_slug,**params)
        
        return_set = []
        
        for content_item in results.items:
            try:
                record = AxilentContentRecord.objects.get(axilent_content_type=content_item.content_type,
                                                          axilent_content_key=content_item.key)
                return_set.append(record.get_local_model())
            except AxilentContentRecord.DoesNotExist:
                log.warn('No local record of %s:%s, referenced by Content Channel %s' % (axl_content_type,content_item.key,self.name))
            
        return return_set
    
    def __call__(self,queryset,channel=None,profile=None,basekey=None,flavor=None,limit=0):
        """
        Function hook - passes through to get_content.
        """
        return self.get_content(queryset,channel=channel,profile=profile,basekey=basekey,flavor=flavor,limit=limit)

# ===========================================
# = Manager class provides Search Interface =
# ===========================================
class ContentManager(Manager):
    """
    A Manager class that provides access to the ACE search interface and content channels.
    """
    def __init__(self,channel=None,flavor=None,limit=0):
        super(ContentManager,self).__init__()
        
        if channel:
            self._channel = ContentChannel(channel=channel,flavor=flavor,limit=limit)
        else:
            self._channel = ContentChannel()
    
    def search(self,query):
        """
        Returns models that correspond to the search results.
        """
        from djax.models import AxilentContentRecord
        return AxilentContentRecord.objects.search(self.model,query)
    
    def channel(self,channel=None,profile=None,basekey=None,flavor=None,limit=0):
        """
        Gets content matching the channel results
        """
        if not self._channel.name and not channel:
            raise ValueError('Content Channel not defined.  You must either specify it as an argument, or pass a default channel to the constructor.')
        
        return self._channel(self.all(),channel=channel,profile=profile,basekey=basekey,flavor=flavor,limit=limit)
        
