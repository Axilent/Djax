"""
Mixins to bind the local models to Axilent calendar functionality.
"""
from djax.calendar.models import CalendarEvent, CalendarResource
from django.contrib.contenttypes.models import ContentType

class AxilentCalendarEvent(object):
    """
    Adds calendar event sync functionality for the local model.
    """
    def push_event(self,start,end,recurrence_quantity=None,recurrence_unit=None,recurrence_end=None,resources=None):
        """
        Pushes the associated event to Axilent.  Should be called AFTER saving the local event model.
        """
        cal_event = None
        try:
            cal_event = CalendarEvent.objects.get_event_for_model(self)
            cal_event.start = start
            cal_event.end = end
            cal_event.recurrence_quantity = recurrence_quantity
            cal_event.recurrence_unit = recurrence_unit
            cal_event.recurrence_end = recurrence_end
            cal_event.save()
        except CalendarEvent.DoesNotExist:
            ctype = ContentType.objects.get_for_model(self)
            
            cal_event = CalendarEvent.objects.create(calendar=self.Axilent.calendar,
                                                     start=start,
                                                     end=end,
                                                     recurrence_quantity=recurrence_quantity,
                                                     recurrence_unit=recurrence_unit,
                                                     recurrence_end=recurrence_end,
                                                     local_content_type=ctype,
                                                     local_id=self.pk)
        
        cal_event.push_to_axilent(resource_models=resources)
    
    def delete_event(self):
        """
        Deletes the associated event in the Axilent calendar.
        """
        try:
            cal_event = CalendarEvent.objects.get_event_for_model(self)
            cal_event.delete_event() # deletes on server
            cal_event.delete()
            return True
        except CalendarEvent.DoesNotExist:
            return False
    
    def get_event(self):
        """
        Gets the matching calendar event, or None if the event has not yet been pushed.
        """
        try:
            return CalendarEvent.objects.get_event_for_model(self)
        except CalendarEvent.DoesNotExist:
            return None

class AxilentCalendarResource(object):
    """
    A mixin for local models that are to be considered calendar resources.
    """
    def push_resource(self):
        """
        Creates the equivilent resource object on Axilent corresponding to the local model.
        """
        resource = CalendarResource.objects.resource_for_model(self)
        return resource.sync()
    
    def resource_profile(self):
        """
        Gets the resource profile for this resource.
        """
        try:
            return CalendarResource.objects.resource_for_model(self).profile
        except CalendarResource.DoesNotExist:
            return None
