"""
Content sync for Djax
"""
from djax.registry import content_registry
from djax.gateway import content_client
import uuid

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

# ======================
# = Content Operations =
# ======================

def sync_content(token=None):
    """
    Synchronizes the local models with Axilent content.
    """
    from djax.models import AxilentContentRecord, ContentSyncLock
    
    if ContentSyncLock.objects.all().exists():
        return False # already sync locked
    
    if not token:
        token = uuid.uuid4().hex
    
    lock = ContentSyncLock.objects.create(token=token)

    for content_type in content_registry.keys():
        content_keys = content_client.content_keys(content_type)
        
        for content_key in content_keys:
            try:
                record = AxilentContentRecord.objects.get(axilent_content_type=content_type,
                                                          axilent_content_key=content_key)
                
                axilent_content = record.get_update()
                if axilent_content:
                    record.sync_content(axilent_content)
            except AxilentContentRecord.DoesNotExist:
                # the axilent content does not exist locally - create
                AxilentContentRecord.objects.create_model(content_type,content_key)
    
    lock.delete()
    return True # sync occured
