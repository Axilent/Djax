"""
For calendar module.
"""
from pax.content import ContentImage
from dateutil import parser

class EventImage(object):
    """
    Local wrapper for event data.
    """
    def __init__(self,data):
        self.content = ContentImage(data['content'])
        self.calendar = data['calendar']
        self.event_type = data['event_type']
        self.start = parser.parse(data['start'])
        self.end = parser.parse(data['end'])
    
    def __getattr__(self,attribute):
        return getattr(self.content,attribute)

class ResourceImage(object):
    """
    Local wrapper for a resource.
    """
    def __init__(self,data):
        self.profile = data['profile']
        self.name = data['name']

class ResourceAvailabilityBlock(object):
    """
    Wraps availability for a resource.
    """
    def __init__(self,profile,start,end):
        self.profile = profile
        self.start = start
        self.end = end

class AggregateAvailabiltyBlock(object):
    """
    Wrapps aggregate availability.
    """
    def __init__(self,start,end):
        self.start = start
        self.end = end

class AvailabilityImage(object):
    """
    Local wrapper for data indicating resource availability.
    """
    def __init__(self,data):
        self.availabilty = [AggregateAvailabilityBlock(avail['start'],avail['end']) for avail in data['availability']]
        self.resources = {}
        for key,value in data['by-resource']:
            self.resources[key] = [ResourceAvailabilityBlock(key,avail['start'],avail['end']) for avail in value]

class CalendarClient(object):
    """
    Client for Calendar API.
    """
    def __init__(self,axilent_connection):
        self.event_resource = axilent_connection.resource_client('axilent.plugins.calendar','event')
        self.calendar_resource = axilent_connection.resource_client('axilent.plugins.calendar','calendar')
        self.resource_resource = axilent_connection.resource_client('axilent.plugins.calendar','resource')
        
        self.api = axilent_connection.http_client('axilent.plugins.calendar')
    
    def get_event(self,calendar,key):
        """
        Gets the specified event.
        """
        data = self.event_resource.get(params={'calendar':calendar,'key':key})
        return EventImage(data)
    
    def create_event(self,
                     calendar,
                     event_type,
                     start,
                     end,
                     content,
                     recurrence_quantity=None,
                     recurrence_unit=None,
                     recurrence_end=None,
                     resources=None):
        """
        Creates a new event.
        """
        response = self.event_resource.post(data={'calendar':calendar,
                                                    'event_type':event_type,
                                                    'start':start.strftime('%Y-%m-%d %H:%M:%S'),
                                                    'end':end.strftime('%Y-%m-%d %H:%M:%S'),
                                                    'content':content,
                                                    'recurrence_quantity':recurrence_quantity,
                                                    'recurrence_unit':recurrence_unit,
                                                    'recurrence_end':recurrence_end,
                                                    'resources':resources})
        
        return response['event-created']
    
    def update_event(self,
                     calendar,
                     key,
                     event_type=None,
                     start=None,
                     end=None,
                     recurrence_quantity=None,
                     recurrence_unit=None,
                     recurrence_end=None,
                     content=None):
        """
        Updates an existing event.
        """
        response = self.event_resource.put(data={'calendar':calendar,
                                                   'key':key,
                                                   'event_type':event_type,
                                                   'start':start.strftime('%Y-%m-%d %H:%M:%S'),
                                                   'end':end.strftime('%Y-%m-%d %H:%M:%S'),
                                                   'recurrence_quantity':recurrence_quantity,
                                                   'recurrence_unit':recurrence_unit,
                                                   'recurrence_end':recurrence_end,
                                                   'content':content})
    
    def delete_event(self,calendar,key):
        """
        Deletes the event.
        """
        self.event_resource.delete(params={'calendar':calendar,'key':key})
    
    def clear_event_recurrence(self,calendar,key):
        """
        Clears recurrence on an event.
        """
        response = self.api.cleareventrecurrence(calendar=calendar,key=key)
        if response['event-recurrence'] == 'cleared':
            return True
        else:
            return False
    
    def list_events(self,calendar,start,end,event_types=None,resources=None,ical=False):
        """
        Gets a list of events for the specified calendar, within the specified date range.
        
        If event types are specified only events of those event types will be returned.
        If resources are specified, only resources where there are bookings matching the
        specified resources will be returned.
        """
        response = self.api.listevents(calendar=calendar,
                                       start=start.strftime('%Y-%m-%d %H:%M:%S'),
                                       end=end.strftime('%Y-%m-%d %H:%M:%S'),
                                       event_types=event_types,
                                       resources=resources,
                                       render_ical=unicode(ical))
        
        return response
    
    def list_calendars(self):
        """
        Lists the calendars.
        """
        return self.calendar_resource.get()
    
    def create_calendar(self,calendar):
        """
        Creates a calendar.
        """
        self.calendar_resource.post(params={'calendar':calendar})
    
    def delete_calendar(self,calendar):
        """
        Deletes the calendar.
        """
        self.calendar_resource.delete(params={'calendar':calendar})
    
    def get_resource(self,profile):
        """
        Gets the specified resource.
        """
        response = self.resource_resource.get(params={'profile':profile})
        return ResourceImage(response)
    
    def create_resource(self,profile,name):
        """
        Creates a resource.
        """
        response = self.resource_resource.post(params={'profile':profile,'name':name})
        return response['resource-created'] # returns the profile key for the created resource
    
    def update_resource(self,profile,name):
        """
        Updates a resource.
        """
        self.resource_resource.put(params={'profile':profile,'name':name})
    
    def delete_resource(self,profile):
        """
        Deletes the resource.
        """
        self.resource_resource.delete(params={'profile':profile})
    
    def list_events_by_date_range(self,calendars,start,end,resources=None,event_types=None):
        """
        Lists the specified events.
        """
        response = self.api.listeventsbydaterange(calendars=calendars,
                                                  start=start,
                                                  end=end,
                                                  resources=resources,
                                                  event_types=event_types)
        
        return [EventImage(event) for event in response]
    
    def list_events_for_month(self,calendars,year,month,resources=None,event_types=None):
        """
        Lists events for the month.
        """
        response = self.api.listeventsformonth(calendars=calendars,
                                               year=year,
                                               month=month,
                                               resources=resources,
                                               event_types=event_types)
        
        return [EventImage(event) for event in response]
    
    def list_events_for_week(self,calendars,year,week,resources=None,event_types=None):
        """
        Lists events for the week.
        """
        response = self.api.listeventsforweek(calendars=calendars,
                                              year=year,
                                              week=week,
                                              resources=resources,
                                              event_types=event_types)
        
        return [EventImage(event) for event in response]
    
    def get_availability_by_date_range(self,calendars,resources,start,end):
        """
        Gets resource availability within the specified date range.
        """
        response = self.api.getavailabilitybydaterange(calendars=calendars,
                                                       resources=resources,
                                                       start=start,
                                                       end=end)
        
        return AvailabilityImage(response)
    
    
    def get_availability_for_month(self,calendars,resources,year,month):
        """
        Gets resource availability for the specified month.
        """
        response = self.api.getavailabilityformonth(calendars=calendars,
                                                    resources=resources,
                                                    year=year,
                                                    month=month)
        
        return AvailabilityImage(response)
    
    def get_availability_for_week(self,calendars,resources,year,week):
        """
        Gets resources availability for the specified week.
        """
        response = self.api.getavailabilityforweek(calendars=calendars,
                                                   resources=resources,
                                                   year=year,
                                                   month=month)
        
        return AvailabilityImage(response)
