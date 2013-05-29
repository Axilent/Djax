"""
Local API for messaging plugin.
"""

class MessagingClient(object):
    """
    Client for messaging system.
    """
    def __init__(self,axilent_connection):
        """
        Constructor.
        """
        self.message_resource = axilent_connection.resource_client('axilent.plugins.messaging','message')
        self.recipient_resource = axilent_connection.resource_client('axilent.plugins.messaging','recipient')
        self.received_message_resource = axilent_connection.resource_client('axilent.plugins.messaging','receivedmessage')
        self.api = axilent_connection.http_client('axilent.plugins.messaging')
    
    def create_message(self,bus,message_type,sender,content):
        """
        Creates a new message.
        """
        response = self.message_resource.post(data={'bus':bus,
                                                    'message_type':message_type,
                                                    'sender':sender,
                                                    'content':content})
        return response['created']
    
    def create_recipient(self,bus,recipient_type,content):
        """
        Creates a new recipient.
        """
        response = self.recipient_resource.post(data={'bus':bus,
                                                      'recipient_type':recipient_type,
                                                      'content':content})
        return response['created']
    
    def update_recipient(self,key,content):
        """
        Updates an existing recipient.
        """
        response = self.recipient_resource.put(data={'key':key,
                                                     'content':content})
        
        return response['updated']
    
    def get_recipient(self,key):
        """
        Gets the specified recipient.
        """
        response = self.recipient_resource.get(params={'key':key})
        return response['content']
    
    def delete_recipient(self,key):
        """
        Deletes the specified recipient.
        """
        response = self.recipient_resource.delete(params={'key':key})
        return response['deleted']
    
    
    def publish_message(self,key,topic):
        """
        Publishes the specified message on the topic.
        """
        response = self.api.publishmessage(key=key,topic=topic)
        return response['sent']
    
    def send_message(self,message_key,recipient_key):
        """
        Point to point sending of the message to the specified recipient.
        """
        response = self.api.sendmessage(message_key=message_key,recipient_key=recipient_key)
        return response['sent']
    
    def inbox(self,recipient_key,unread_only=True):
        """
        Gets the inbox messages for the recipient.
        """
        unread_string = 'True' if unread_only else 'False'
        response = self.api.inbox(recipient_key=recipient_key,unread_only=unread_string)
        return response['received-messages']
    
    def get_received_message(self,recipient_key,message_key):
        """
        Gets the received message for the recipient.
        """
        return self.received_message_resource.get(params={'recipient_key':recipient_key,'message_key':message_key})
        
    def update_received_message(self,recipient_key,message_key,read=True):
        """
        Updates the received message (changing the 'read' status).
        """
        read_string = 'True' if read else 'False'
        response = self.received_message_resource.put(params={'recipient_key':recipient_key,'message_key':message_key,'read':read_string})
        return bool(response['message-read'])
    
    def delete_received_message(self,recipient_key,message_key):
        """
        Deletes the received message.
        """
        response = self.received_message_resource.delete(params={'recipient_key':recipient_key,'message_key':message_key})
        return response['message-deleted']
    
    def subscribe(self,recipient_key,topic):
        """
        Subscribes the recipient to the topic.
        """
        response = self.api.subscribe(recipient_key=recipient_key,topic=topic)
        return response['topic-subscribed']
    
    def unsubscribe(self,recipient_key,topic):
        """
        Unsubscribes the recipient from the topic.
        """
        response = self.api.unsubscribe(recipient_key=recipient_key,topic=topic)
        return response['topic-subscribed']

        