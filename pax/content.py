"""
Content API.
"""
from pax.exceptions import PaxException
from pax.util import slugify
from dateutil import parser

class ContentImage(object):
    """
    Wrapper for content item from Axilent.
    """
    def __init__(self,data):        
        content = None
        
        if 'endorsement' in data:
            # this is a policy result
            self.endorsement = data['endorsement']
            content = data['content']
        else:
            self.endorsement = 0
            content = data
        
        self.content_type = content['content_type']
        self.key = content['key']
        self.data = content['data']
    
    def __getattr__(self,attribute):
        """
        Fallback to data access
        """
        try:
            return self.data[attribute]
        except KeyError:
            raise AttributeError

class ChannelResult(object):
    """
    Wrapper for content channel result.
    """
    def __init__(self,data):
        items = None
        if hasattr(data,'keys'):
            # this is a policy result
            items = data['default']
            self.flavor = data['meta']['flavor']
            self.channel = data['meta']['channel']
        else:
            self.flavor = None
            self.channel = None
        
        self.items = [ContentImage(item_data) for item_data in items]
    
    def __iter__(self):
        return self.items

class ContentClient(object):
    """
    Content client.
    """
    def __init__(self,axilent_connection):
        self.content_resource = axilent_connection.resource_client('axilent.content','content')
        self.api = axilent_connection.http_client('axilent.content')
    
    def get_content(self,content_type,key):
        """
        Gets the specified content item.
        """
        data = self.content_resource.get(params={'content_type_slug':slugify(content_type),'content_key':key})
        return ContentImage(data)
    
    def channel_group(self,group,profile=None,basekey=None,limit=None,flavor=None):
        """
        Gets content from a Content Channel Group.
        """
        response = self.api.contentchannelgroup(group=group,profile=profile,basekey=basekey,limit=limit,flavor=flavor)
        return ChannelResult(response)
    
    def search(self,query,*content_types):
        """
        Searches for content.
        """
        content_type_list = ','.join([slugify(ctype) for ctype in content_types])
        response = self.api.search(query=query,content_types=content_type_list)
        return ChannelResult(response)
    
    def channel(self,channel_name,profile=None,basekey=None,limit=None,flavor=None):
        """
        Gets content from a Content Channel.
        """
        response = self.api.contentchannel(channel=channel_name,profile=profile,basekey=basekey,limit=limit,flavor=flavor)
        return ChannelResult(response)
    
    def content_keys(self,content_type):
        """
        Gets a list of keys for content of the specified type.
        """
        return self.api.getcontentkeys(content_type_slug=slugify(content_type))

    def get_content_by_unique_field(self,content_type,field_name,field_value):
        """
        Gets a content item matching the specified field value.
        """
        data = self.api.getcontentbyuniquefield(content_type=slugify(content_type),field_name=field_name,field_value=field_value)
        return ContentImage(data)
    
    def latest_update(self,content_type,content_key):
        """
        Gets the date of the latest update.
        """
        response = self.api.latestupdate(content_type_slug=slugify(content_type),content_key=content_key)
        return parser.parse(response['updated']) if response['updated'] else None
