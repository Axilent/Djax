"""
Mixins to bind the local models to Axilent calendar functionality.
"""
from djax.calendar.models import CalendarEvent

class AxilentCalendarEvent(object):
    """
    Adds calendar event sync functionality for the local model.
    """
    def push_event(self,start,end,recurrence_quantity=None,recurrence_unit=None,recurrence_end=None):
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
            cal_event = CalendarEvent.objects.create(calendar=self.Axilent.calendar,
                                                     start=start,
                                                     end=end,
                                                     recurrence_quantity=recurrence_quantity,
                                                     recurrence_unit=recurrence_unit,
                                                     recurrence_end=recurrence_end)
        
        cal_event.push_to_axilent()
