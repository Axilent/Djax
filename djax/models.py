"""
Models for Djax.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
import logging
from datetime import datetime
from djax.gateway import content_client
from djax.registry import content_registry, build_registry

log = logging.getLogger('djax')

class AxilentContentRecordManager(models.Manager):
    """
    Manager class for AxilentContentRecord.
    """
    def get_record(self,model):
        """
        Gets the record for the specified model.
        """
        content_type = ContentType.objects.get_for_model(model)
        return self.get(local_content_type=content_type,local_id=model.pk)
    
    def create_model(self,axilent_content_type,axilent_content_key):
        """
        Creates a new model and accompaning content record for the axilent content.
        """
        content_data = content_client.get_content(axilent_content_type,axilent_content_key)
        model_class = content_registry[axilent_content_type]
        
        field_map = {}
        try:
            field_map = model_class.Axilent.field_map
        except AttributeError:
            for key in content_data.data.keys():
                field_map[key] = key
        
        fields = {}
        for axilent_field,model_field in field_map.items():
            try:
                fields[model_field] = content_data.data[axilent_field]
            except KeyError:
                pass
        
        local_model = model_class.objects.create(**fields) # create the local model with the content data
        local_content_type = ContentType.objects.get_for_model(local_model)
        record = self.create(local_content_type=local_content_type,
                             local_id=local_model.pk,
                             axilent_content_type=axilent_content_type,
                             axilent_content_key=axilent_content_key,
                             updated=datetime.now())
        
        return (local_model,record)

class AxilentContentRecord(models.Model):
    """
    Mapping for a specific Axilent content item to a model.
    """
    local_content_type = models.ForeignKey(ContentType,related_name='axilent_content_records')
    local_id = models.IntegerField()
    axilent_content_type = models.CharField(max_length=100)
    axilent_content_key = models.CharField(max_length=100)
    updated = models.DateTimeField(null=True)
    
    objects = AxilentContentRecordManager()
    
    def update_available(self):
        """
        Determines if a new content update is available from Axilent.
        """
        if content_client.latest_update(self.axilent_content_type,self.axilent_content_key):
            return True
        else:
            return False

    def get_update(self):
        """
        Gets the updated content from Axilent.
        """
        return content_client.latest_update(self.axilent_content_type,self.axilent_content_key)
    
    def sync_content(self,axilent_content):
        """
        Syncs the local content to the incoming axilent content (a dictionary).
        """
        local_class = self.local_content_type.model_class()
        local_model = local_class.objects.get(pk=self.local_id)
        field_map = {}
        excludes = []
        
        # collect mappings
        if hasattr(local_class,'Axilent'):
            if hasattr(local_class.Axilent,'field_map'):
                field_map = local_class.Axilent.field_map
            
            if hasattr(local_class.Axilent,'exclude'):
                excludes = local_class.Axilent.exclude
        
        # Default the field map to the axilent fields
        if not field_map:
            for key in axilent_content.data.keys():
                field_map[key] = key
        
        # Iterate through the field map and set the local model values from the incoming Axilent content
        for axilent_field, model_field in field_map.items():
            try:
                value = getattr(axilent_content,axilent_field)
                setattr(local_model,model_field,value)
            except AttributeError:
                log.exception('There is a mis-matched field')
            
        
        local_model.save()
        self.updated = datetime.now()
        self.save()
        
        return local_model
    
    def get_local_model(self):
        """
        Gets the local model for this record.
        """
        return self.local_content_type.model_class().objects.get(pk=self.local_id)
    
    class Meta:
        unique_together = (('local_content_type','local_id'),('axilent_content_type','axilent_content_key'))

class ContentSyncLock(models.Model):
    """
    Lock for a content sync.  Indicates a sync is under way.
    """
    token = models.CharField(max_length=100)


# =================
# = Registry Hook =
# =================
build_registry()