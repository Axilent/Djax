"""
Models for Djax.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
import logging
from datetime import datetime
from djax.gateway import content_client, library_client, library_project
from djax.registry import content_registry, build_registry
import re

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
    
    def field_map(self,model,axilent_content={}):
        """
        Gets the field map for the model.
        """
        field_map = {}
        excludes = []
        
        # collect mappings
        if hasattr(model,'Axilent'):
            if hasattr(model.Axilent,'field_map'):
                field_map = model.Axilent.field_map
            
            if hasattr(model.Axilent,'exclude'):
                excludes = model.Axilent.exclude
        
        # Default the field map to the axilent fields
        if not field_map:
            for key in axilent_content.data.keys():
                if not key in excludes:
                    field_map[key] = key
        
        return field_map
    
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
    
    def model_to_content_link(self,value):
        """
        Converts a local model (held as a foreign key reference) to an Axilent
        content link in <content-type>:<content-key> format.
        """
        if isinstance(value,models.Model):
            try:
                record = self.get_record(value)
                return '%s:%s' % (record.axilent_content_type,record.axilent_content_key)
            except AxilentContentRecord.DoesNotExist:
                return ''
        else:
            return value
    
    def content_link_to_model(self,value):
        """
        Converts a content link format string '<content-type>:<content-key>' to a local
        model to be used as a foreign key.
        """
        if re.match(r'^[\w\s]+:[A-Fa-f0-9]+$',value):
            ctype, ckey = value.split(':')
            record = self.get(axilent_content_type=ctype,axilent_content_key=ckey)
            return record.get_local_model()
        else:
            return value
    
    def data_for_library(self,model):
        """
        Gets a data dictionary prepared for the library.
        """
        lib_data = {}
        field_map = self.field_map(model)
        for axilent_field, model_field in field_map.items():
            try:
                lib_data[axilent_field] = self.model_to_content_link(getattr(model,model_field))
            except AttributeError:
                log.exception('Local model has no field %s (matched to Axilent field %s).' % (model_field,axilent_field))
        
        return lib_data
    
    def push_to_library(self,model):
        """
        Pushes the model to the Axilent library (assuming the library integration is active).
        
        Returns a 2-tuple of booleans indicating 1.  If the library was updated and 2. If the
        content item was created on Axilent for the first time.
        
        """
        if library_client:
            lib_data = self.data_for_library(model)
            try:
                record = self.get_record(model)
                # this content item already exists on Axilent - update
                response = library_client.update_content(record.axilent_content_type,
                                                         library_project,
                                                         record.axilent_content_key,
                                                         **lib_data)
                return (True,False)
            except AxilentContentRecord.DoesNotExist:
                # this is new
                local_content_type = ContentType.objects.get_for_model(model)
                axilent_content_type = model.Axilent.content_type
                response = library_client.create_content(axilent_content_type,
                                                         library_project,
                                                         **lib_data)
                returned_content_type, returned_key = response.split(':')
                
                # create new record
                self.create(local_content_type=local_content_type,
                            local_id=model.pk,
                            axilent_content_type=axilent_content_type,
                            axilent_content_key=returned_key)
                
                return (True,True)
        else:
            return (False,False)

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
        local_model = self.get_local_model()
        field_map = self.field_map()
        
        # Iterate through the field map and set the local model values from the incoming Axilent content
        for axilent_field, model_field in field_map.items():
            try:
                value = getattr(axilent_content,axilent_field)
                setattr(local_model,model_field,self.content_link_to_model(value))
            except AttributeError:
                log.exception('Local model has no field %s (matched to Axilent field %s).' % (model_field,axilent_field))
        
        local_model.save()
        self.updated = datetime.now()
        self.save()
        
        return local_model
    
    def get_local_model(self):
        """
        Gets the local model for this record.
        """
        return self.local_content_type.model_class().objects.get(pk=self.local_id)
    
    def archive(self):
        """
        Archives the content on Axilent.
        """
        return library_client.archive_content(library_project,self.axilent_content_type,self.axilent_content_key)
    
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