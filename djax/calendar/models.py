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

calendar_client = CalendarClient(cx)

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
    
    def _get_event_type(self):
        try:
            model_class = self.local_content_type.model_class()
            return model_class.Axilent.event_type
        except AttributeError:
            raise ValueError('For the local model %s you must set the Axilent event type.' % self.local_content_type.name)
    
    def push_to_axilent(self):
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
            # this is the first time this event has been sync'd
            content_key = calendar_client.create_event(self.calendar,
                                                       event_type,
                                                       self.start,
                                                       self.end,
                                                       local_model.content_dict(),
                                                       recurrence_quantity=self.recurrence_quantity,
                                                       recurrence_unit=self.recurrence_unit,
                                                       recurrence_end=self.recurrence_end)
            
            record = AxilentContentRecord.objects.create(local_content_type=self.local_content_type,
                                                         local_id=self.local_id,
                                                         axilent_content_type=local_model.Axilent.content_type,
                                                         axilent_content_key=content_key,
                                                         updated=datetime.now())