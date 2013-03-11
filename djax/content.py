"""
Content sync for Djax
"""
from djax.models import AxilentContentRecord, ContentSyncLock
from djax.registry import content_registry
from djax.gateway import get_content_keys
import uuid

class AxilentContent(object):
    """
    Mixin to provide Axilent content sync services for Django models.
    """
    def sync_with_axilent(self):
        """
        Synchronizes the local content with the latest from Axilent.
        """
        # 1. Check status of content at Axilent project.  Abort if not updated later than ContentRecord.
        record = AxilentContentRecord.objects.get_record(self)
        if record.update_available():
            axilent_content = record.get_update() # 2. get the updated content from Axilent
            record.sync_content(axilent_content) # 3. write to the local model

# ======================
# = Content Operations =
# ======================

def sync_content(token=None):
    """
    Synchronizes the local models with Axilent content.
    """
    if ContentSyncLock.objects.all().exists():
        return False # already sync locked
    
    if not token:
        token = uuid.uuid4().hex
    
    lock = ContentSyncLock.objects.create(token=token)

    for content_type in content_registry.keys():
        content_keys = get_content_keys(content_type)
        
        for content_key in content_keys:
            try:
                record = AxilentContentRecord.objects.get(axilent_content_type=content_type,
                                                          axilent_content_key=content_key)
                
                if record.update_available():
                    axilent_content = record.get_update()
                    record.sync_content(axilent_content)
            except AxilentContentRecord.DoesNotExist:
                # the axilent content does not exist locally - create
                AxilentContentRecord.objects.create_model(content_type,content_key)
    
    lock.delete()
    return True # sync occured
