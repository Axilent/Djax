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
import re

log = logging.getLogger('djax')

class ACEContent(object):
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
            for axilent_field, local_field in self.ACE.field_map.items():
                try:
                    content_dict[axilent_field] = getattr(self,local_field)
                except AttributeError:
                    raise ValueError('The local field %s is not defined in this model.' % local_field)
            
            return content_dict
        except AttributeError:
            raise ValueError('You must define an ACE field map to create a content dict from a local model.')
    
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
                               slugify(self.ACE.content_type),
                               profile=profile,
                               variables={'key':self.get_axilent_content_key()},
                               environment=environment,
                               identity=identity)
    
    def trigger_ban(self,profile,environment={},identity={}):
        """
        Sends a ban trigger for this content.
        """
        trigger_client.trigger('ban',
                               slugify(self.ACE.content_type),
                               profile=profile,
                               variables={'key':self.get_axilent_content_key()},
                               environment=environment,
                               identity=identity)

# ====================
# = Field Converters =
# ====================
class DefaultFieldConverter(object):
    def __init__(self,local_field):
        self.field = local_field
    
    def to_local_model(self,ace_content,ace_field_value):
        """
        Associated content link, if found, otherwise just assigns value.
        """
        from djax.models import AxilentContentRecord
        if re.match(r'^[\w\s]+:[A-Fa-f0-9]+$',ace_field_value):
            ctype, ckey = ace_field_value.split(':')
            local_model = AxilentContentRecord.objects.get_or_create_model(axilent_content_type=ctype,axilent_content_key=ckey)
            log.debug('Converted content link %s to local model.' % ace_field_value)
            return local_model
        else:
            return ace_field_value
    
    def to_ace(self,local_model):
        """
        Returns the content link string from the model.
        """
        from djax.models import AxilentContentRecord
        value = getattr(local_model,self.field)
        if isinstance(value,models.Model):
            try:
                record = AxilentContentRecord.objects.get_record(value)
                log.debug('Converted local model to content link %s:%s.' % (record.axilent_content_type,record.axilent_content_key))
                return '%s:%s' % (record.axilent_content_type,record.axilent_content_key)
            except AxilentContentRecord.DoesNotExist:
                return ''
        else:
            return value

class NullableForeignKeyConverter(object):
    """
    Special converter to convert content links to local foreign keys. The default
    converter would normally handle this, but not in the case where there is the
    possibility of a nullable foreign key.  If the model has a nullable foreign
    key, this converter should be specified instead.
    """
    def __init__(self,local_field):
        self.field = local_field
    
    def to_local_model(self,ace_content,ace_field_value):
        """
        Associated content link or None.
        """
        from djax.models import AxilentContentRecord
        if ace_field_value:
            if re.match(r'^[\w\s]+:[A-Fa-f0-9]+$',ace_field_value):
                ctype, ckey = ace_field_value.split(':')
                local_model = AxilentContentRecord.objects.get_or_create_model(axilent_content_type=ctype,axilent_content_key=ckey)
                log.debug('Converted content link %s to local model.' % ace_field_value)
                return local_model
            else:
                raise ValueError('Cannot use the NullableForeignKeyConverter to set non-null values that are not foreign keys. Value %s for field %s.' % (ace_field_value,self.field))
        else:
            return None
    
    def to_ace(self,local_model):
        """
        Returns a content link string, or ''.
        """
        from djax.models import AxilentContentRecord
        value = getattr(local_model,self.field)
        if value:
            if isinstance(value,models.Model):
                try:
                    record = AxilentContentRecord.objects.get_record(value)
                    log.debug('Converted local model to content link %s:%s.' % (record.axilent_content_type,record.axilent_content_key))
                    return '%s:%s' % (record.axilent_content_type,record.axilent_content_key)
                except AxilentContentRecord.DoesNotExist:
                    return ''
            else:
                raise ValueError('Cannot use the NullableForeignKeyConverter to set non-null values that are not content links. Value %s for field %s.' & (unicode(value),self.field))
        else:
            return ''

class M2MFieldConverter(object):
    """
    Field converter that translates m-2-m model relations, from ACE content link lists.
    """
    deferred = True
    
    def __init__(self,local_field):
        self.field = local_field
    
    def to_local_model(self,ace_content,ace_field_value,local_model):
        """
        Converts to local model relations.
        """
        from djax.models import AxilentContentRecord
        log.debug('Converting ace value %s to local model relations.' % ace_field_value)
        added_models = []
        for compound_key in ace_field_value:
            ctype, ckey = compound_key.split(':')
            linked_model = AxilentContentRecord.objects.get_or_create_model(axilent_content_type=ctype,
                                                                           axilent_content_key=ckey)
            getattr(local_model,self.field).add(linked_model)
            added_models.append(linked_model.pk)
            log.debug('Building local model relation from content link %s.' % compound_key)
        
        # get rid of any relations not specified in the content link list
        for stale_link in getattr(local_model,self.field).exclude(pk__in=added_models):
            getattr(local_model,self.field).remove(stale_link)
            log.debug('Removing stale link %s from local model.' % unicode(stale_link))
        
        local_model.save()
    
    def to_ace(self,local_model):
        """
        Converts local relations to content key list.
        """
        from djax.models import AxilentContentRecord
        key_list = []
        for linked_model in getattr(local_model,self.field).all():
            try:
                record = AxilentContentRecord.objects.get_record(linked_model)
                key_list.append('%s:%s' % (record.axilent_content_type,record.axilent_content_key))
            except AxilentContentRecord.DoesNotExist:
                log.warning('Cannot assign local model %s to ACE content link list.  Local model does not exist in ACE.' % unicode(linked_model))
        
        return key_list

class WriteNullFieldConverter(DefaultFieldConverter):
    """
    Either writes the value supplied from ACE, or None to the local model.
    """
    accepts_null = True  


# ======================
# = Content Operations =
# ======================

def sync_record(content_type,content_key):
    """
    Syncs a single content record.
    """
    from djax.models import AxilentContentRecord
    record = None
    try:
        record = AxilentContentRecord.objects.get(axilent_content_type=content_type,
                                                  axilent_content_key=content_key)
        axilent_content = record.get_update()
        if axilent_content:
            log.info('Syncing local model %s:%s with updated content from ACE.' % (record.axilent_content_type,record.axilent_content_key))
            record.sync_content(axilent_content)
            return False # no new record created
    except AxilentContentRecord.DoesNotExist:
        AxilentContentRecord.objects.create_model(content_type,content_key)
        return True # new record created

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
                log.debug('Syncing local model %s:%s with updated content from ACE' % (record.axilent_content_type,record.axilent_content_key))
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

def sync_library_to_content_type(content_type):
    """ 
    Syncs the ACE library to the specified content type.
    """
    content_model = content_registry[content_type]
    for item in content_model.objects.all():
        item.push_to_library()

def sync_library(token=None,content_type_to_sync=None):
    """ 
    Synchronizes the ACE library with the local content.
    """
    from djax.models import ContentSyncLock
    
    if ContentSyncLock.objects.all().exists():
        return False
    
    if not token:
        token = uuid.uuid4().hex
    
    lock = ContentSyncLock.objects.create(token=token)
    
    # ensure registry loaded
    build_registry()
    
    if content_type_to_sync:
        log.info('Pushing %s content to ACE library.' % content_type_to_sync)
        try:
            content_type = content_registry[content_type_to_sync]
            sync_library_to_content_type(content_type_to_sync)
        except KeyError:
            log.error('%s is not in the content registry.' % content_type_to_sync)
    else:
        for content_type in content_registry.keys():
            log.info('Pushing %s content to ACE library.' % content_type)
            sync_library_to_content_type(content_type)
    
    lock.delete()
    return True

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
    
    def get_content(self,queryset,channel=None,profile=None,basekey=None,flavor=None,limit=0,include_endorsements=False):
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
        
        axl_content_type = queryset.model.ACE.content_type
        
        results = self.api.channel(channel_slug,**params)
        
        queryset_keys = queryset.values_list('id',flat=True)
        
        return_set = []
        
        for content_item in results.items:
            try:
                record = AxilentContentRecord.objects.get(axilent_content_type=content_item.content_type,
                                                          axilent_content_key=content_item.key,
                                                          local_id__in=queryset_keys)
                if include_endorsements:
                    return_set.append(ContentItemWrapper(record.get_local_model(),content_item.endorsement))
                else:
                    return_set.append(record.get_local_model())
            except AxilentContentRecord.DoesNotExist:
                log.warn('No local record of %s:%s, referenced by Content Channel %s' % (axl_content_type,content_item.key,self.name))
            
        return return_set
    
    def __call__(self,queryset,channel=None,profile=None,basekey=None,flavor=None,limit=0,include_endorsements=False):
        """
        Function hook - passes through to get_content.
        """
        return self.get_content(queryset,channel=channel,profile=profile,basekey=basekey,flavor=flavor,limit=limit,include_endorsements=include_endorsements)

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
    
    def channel_sort(self,queryset,channel=channel,profile=None,basekey=None,flavor=None,limit=0):
        """
        Sorts the passed queryset by rlevel, with the most relevant results first.
        """
        channel_results = self._channel(queryset,channel=channel,profile=profile,basekey=basekey,flavor=flavor,limit=limit,include_endorsements=True)
        remainder_results = queryset.exclude(pk__in=[item.pk for item in channel_results])
        final_results = channel_results + [ContentItemWrapper(item,0) for item in remainder_results]
        final_results.sort(cmp=lambda x,y: cmp(y.rlevel,x.rlevel))
        return final_results
    
    def freeze(self,results):
        """
        Freezes the results, returning a frozen sort key. Results must be
        endorsed content items from channel_sort.
        """
        from djax.models import FrozenSort
        return FrozenSort.objects.freeze(results)
    
    def get_frozen_sort(self,key):
        """
        Gets channels results from a frozen sort.  Will raise FrozenSort.DoesNotExist
        if the key doesn't match any frozen sorts.
        """
        from djax.models import FrozenSort
        fs = FrozenSort.objects.get(key=key)
        return fs.sorted_results()

class ContentItemWrapper(object):
    """
    Wrapper for a content item that contains an rlevel as returned
    by a specific content channel call.
    """
    def __init__(self,item,rlevel):
        object.__setattr__(self,'item',item)
        object.__setattr__(self,'rlevel',rlevel)
    
    def __getattr__(self,name):
        return getattr(self.item,name)
    
    def __setattr__(self,name,value):
        setattr(self.item,name,value)

