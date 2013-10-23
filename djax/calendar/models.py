"""
Models for Djax Calendar - works with Axilent calendar plugin.
"""
from django.db import models
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from djax.models import AxilentContentRecord
from djax.content import AxilentContent
from djax.registry import content_registry
from pax.calendar import CalendarClient
from djax.gateway import cx
import uuid
import logging

log = logging.getLogger('djax')

calendar_client = CalendarClient(cx)

class CalendarEventManager(models.Manager):
    """
    Manager for calendar events.
    """
    def get_event_for_model(self,model):
        """
        Gets the calendar event associated with the specified model.
        """
        ctype = ContentType.objects.get_for_model(model)
        return self.get(local_content_type=ctype,local_id=model.pk)
    
    def list_events(self,calendar,start,end,event_types=None,resources=None,ical=False):
        """
        Lists events between the specified date range for the specified calendar.
        
        If event_types are defined only events matching the specified types will be
        returned.
        
        If resources are specified only events with bookings for the specified 
        resources will be returned.
        """
        resource_keys = None
        if resources:
            resource_keys = [CalendarResource.objects.resource_for_model(resource).profile for resource in resources]
        
        event_keys = calendar_client.list_events(calendar,start,end,event_types=event_types,resources=resource_keys,ical=ical)['events']
        if ical:
            return event_keys # this is actually the icalendar string
        else:
            log.debug('Retrieved %d event keys from Axilent:%s' % (len(event_keys),str(event_keys)))
            records = AxilentContentRecord.objects.filter(axilent_content_key__in=event_keys)
            log.debug('Found %d content records corresponding to event keys.' % records.count())
            return [record.get_local_model() for record in records]
    
    def check_availability(self,calendar,start,end,resources):
        """
        Checks resource availability for the specified date range.  Returns True or False,
        depending on availability.
        """
        events = self.list_events(calendar,start,end,resources=resources)
        return False if events else True

class CalendarEvent(models.Model):
    """
    A local representation of a calendar.
    """
    calendar = models.CharField(max_length=100)
    local_content_type = models.ForeignKey(ContentType,related_name='calendar_events')
    local_id = models.IntegerField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    recurrence_quantity = models.IntegerField(default=0)
    recurrence_unit = models.CharField(blank=True,null=True,max_length=100)
    recurrence_end = models.DateTimeField(blank=True, null=True)
    
    objects = CalendarEventManager()
    
    def _get_event_type(self):
        try:
            model_class = self.local_content_type.model_class()
            return model_class.Axilent.event_type
        except AttributeError:
            raise ValueError('For the local model %s you must set the Axilent event type.' % self.local_content_type.name)
    
    def push_to_axilent(self,resource_models=None):
        """
        Pushes local data to Axilent.
        """
        event_type = self._get_event_type()
        local_model = self.local_content_type.model_class().objects.get(pk=self.local_id)
        
        if not isinstance(local_model,AxilentContent):
            raise ValueError('Event content must extend AxilentContent!')
        
        try:
            record = AxilentContentRecord.objects.get(local_content_type=self.local_content_type,
                                                      local_id=self.local_id)
            
            calendar_client.update_event(self.calendar,
                                         record.axilent_content_key,
                                         event_type=event_type,
                                         start=self.start,
                                         end=self.end,
                                         recurrence_quantity=self.recurrence_quantity,
                                         recurrence_unit=self.recurrence_unit,
                                         recurrence_end=self.recurrence_end,
                                         content=local_model.content_dict())
        
        except AxilentContentRecord.DoesNotExist:
            resources = []
            if resource_models:
                for resource_model in resource_models:
                    resources.append(CalendarResource.objects.resource_for_model(resource_model).profile)
            
            # this is the first time this event has been sync'd
            content_key = calendar_client.create_event(self.calendar,
                                                       event_type,
                                                       self.start,
                                                       self.end,
                                                       local_model.content_dict(),
                                                       recurrence_quantity=self.recurrence_quantity,
                                                       recurrence_unit=self.recurrence_unit,
                                                       recurrence_end=self.recurrence_end,
                                                       resources=resources)
            
            record = AxilentContentRecord.objects.create(local_content_type=self.local_content_type,
                                                         local_id=self.local_id,
                                                         axilent_content_type=local_model.Axilent.content_type,
                                                         axilent_content_key=content_key,
                                                         updated=datetime.now())
        
    def delete_event(self):
        """
        Deletes the event on Axilent.
        """
        try:
            record = AxilentContentRecord.objects.get(local_content_type=self.local_content_type,
                                                      local_id=self.local_id)
            calendar_client.delete_event(self.calendar,record.axilent_content_key)
            record.delete()
            return True
        except AxilentContentRecord.DoesNotExist:
            return False
    
    def to_dict(self):
        """
        Returns a dictionary representation of this calendar event.
        """
        return {'calendar':self.calendar,
                'start':self.start,
                'end':self.end,
                'recurrence_quantity':self.recurrence_quantity,
                'recurrence_unit':self.recurrence_unit,
                'recurrence_end':self.recurrence_end}
    
    class Meta:
        unique_together = (('local_content_type','local_id'),)


class CalendarResourceManager(models.Manager):
    """
    Manager class for CalendarResource.
    """
    def resource_for_model(self,model):
        """
        Gets a resource for the specified model.
        """
        ctype = ContentType.objects.get_for_model(model)
        try:
            return self.get(local_content_type=ctype,local_id=model.pk)
        except CalendarResource.DoesNotExist:
            return self.create(profile=uuid.uuid4().hex,local_content_type=ctype,local_id=model.pk)
    

class CalendarResource(models.Model):
    """
    A resource - someone or something that can be booked on a calendar.
    """
    profile = models.CharField(unique=True, max_length=100)
    local_content_type = models.ForeignKey(ContentType,related_name='calendar_resources')
    local_id = models.IntegerField(unique=True)
    
    objects = CalendarResourceManager()
    
    def get_local(self):
        """
        Gets the local model for this resource.
        """
        return self.local_content_type.model_class().objects.get(pk=self.local_id)
    
    def sync(self):
        """
        Synchronizes this resource on Axilent.
        """
        try:
            calendar_client.get_resource(self.profile)
        except:
            # not there - create
            calendar_client.create_resource(self.profile,'%s:%d' % (self.local_content_type.name,self.local_id))
    
    class Meta:
        unique_together = (('local_content_type','local_id'),)
