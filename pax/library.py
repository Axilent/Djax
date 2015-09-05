"""
Client for the library API.
"""

class LibraryClient(object):
    """
    Library API client.
    """
    def __init__(self,axilent_connection):
        self.__content_resource = None
        self.axilent_connection = axilent_connection
        self.api = axilent_connection.http_client('axilent.library')

    @property
    def content_resource(self):
        if self.__content_resource is None:
            self.__content_resource = self.axilent_connection.resource_client(
                'axilent.library', 'content')
        return self.__content_resource

    def create_content(self,content_type,project,search_index=True,**field_data):
        """
        Creates the content.  Returns the new content item key in the format:

        <content-type>:<content-key>
        """
        response = self.content_resource.post(data={'content_type':content_type,
                                                    'project':project,
                                                    'search_index':search_index,
                                                    'content':field_data})
        return response['created_content']

    def update_content(self,content_type,project,content_key,search_index=True,reset_workflow=True,**field_data):
        """
        Updates existing content.
        """
        response = self.content_resource.put(data={'content_type':content_type,
                                                   'project':project,
                                                   'key':content_key,
                                                   'search_index':search_index,
                                                   'reset_workflow':reset_workflow,
                                                   'content':field_data})
        return response['updated_content']

    def ping(self,project,content_type):
        """
        Tests connection with Axilent.
        """
        return self.api.ping(project=project,content_type=content_type)

    def index_content(self,project,content_type,content_key):
        """
        Forces re-indexing of the specified content item.
        """
        response = self.api.indexcontent(content_key=content_key,
                                         project=project,
                                         content_type=content_type)
        return response['indexed']

    def tag_content(self,project,content_type,content_key,tag,search_index=True):
        """
        Tags the specified content item.
        """
        response = self.api.tagcontent(project=project,
                                       content_type=content_type,
                                       content_key=content_key,
                                       tag=tag,
                                       search_index=search_index)
        return response['tagged_content']

    def detag_content(self,project,content_type,content_key,tag,search_index=True):
        """
        De-tags the specified content item.
        """
        response = self.api.detagcontent(project=project,
                                         content_type=content_type,
                                         content_key=content_key,
                                         tag=tag,
                                         search_index=search_index)
        return response['removed_tag']

    def archive_content(self,project,content_type,content_key):
        """
        Archives the content on Axilent.
        """
        response = self.content_resource.delete(params={'content_type':content_type,
                                                        'project':project,
                                                        'key':content_key})
        return response['archived']
