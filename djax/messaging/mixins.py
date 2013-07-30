"""
Mixins for messaging functionality.
"""
from djax.messaging.models import Recipient, Message, ReceivedMessage
from django.db import models

class AxilentRecipient(object):
    """
    Provides functionality for a sender / receiver of a message.
    """
    def push_recipient(self):
        """
        Creates the sender on Axilent.
        """
        return Recipient.objects.push_recipient(self)
    
    def get_recipient(self):
        """
        Gets the recipient.  Will raise exception if the
        recipient hasn't yet been pushed to Axilent.
        """
        return Recipient.objects.get_recipient(self)
    
    def inbox(self,*message_models,**filters):
        """
        Gets received messages for this recipient.
        """
        recipient = Recipient.objects.get_recipient(self)
        return recipient.inbox(*message_models,**filters)
    
    def mark_all_read(self):
        """
        Marks all received messages for this recipient as read.
        """
        recipient = Recipient.objects.get_recipient(self)
        recipient.mark_all_read()
    
    def subscribe(self,topic):
        """
        Subscribes this recipient to a topic.
        """
        recipient = Recipient.objects.get_recipient(self)
        recipient.subscribe(topic)
    
    def unsubscribe(self,topic):
        """
        Unsubscribes this recipient from the topic.
        """
        recipient = Recipient.objects.get_recipient(self)
        recipient.unsubscribe(topic)

class MessageNotReceived(Exception):
    """
    Indicates the message was not received.
    """    

class AxilentMessage(object):
    """
    Provides message functionality for a Django model.
    """
    def create_message(self,sender):
        """
        Creates the message in the Axilent messaging bus.  The sender is
        a recipient implementing model representing the party that sent
        the message.
        """
        sender_recip = sender.push_recipient()
        return Message.objects.create_message(self,sender_recip)
    
    def publish_message(self,topic):
        """
        Publishes the message to the specified topic.
        """
        message = Message.objects.message_for_model(self)
        message.publish(topic)
    
    def send_message(self,recipient):
        """
        Sends a message to the specified recipient.  The recipient is
        a Recipient implementing model representing the receiver of
        the message.
        """
        recip = recipient.get_recipient()
        message = Message.objects.message_for_model(self)
        message.send(recip)
    
    def mark(self,recipient,read=True):
        """
        Marks the message as read or unread for the specified recipient.
        The recipient is a Recipient implementing model representing the
        receiver of the message.
        """
        recip = recipient.get_recipient()
        message = Message.objects.message_for_model(self)
        message.update_received(recip,read=read)
    
    def delete_received(self,recipient):
        """
        Deletes the received version of this message for the specified
        recipient.  The recipient is a Recipient implementing model
        representing the receiver of the message.
        """
        recip = recipient.get_recipient()
        message = Message.objects.message_for_model(self)
        message.delete_received(recip)
    
    def get_received(self,recipient):
        """
        Gets the received message for the specified recipient.  If the
        recipient has not received the message, will raise an exception.
        """
        try:
            recip = recipient.get_recipient()
            message = Message.objects.message_for_model(self)
            return ReceivedMessage.objects.get(message=message,recipient=recip)
        except ReceivedMessage.DoesNotExist:
            raise MessageNotReceived

class MailSearchManager(models.Manager):
    """
    Adds mail search functionality.
    """
    def search(self,query):
        """
        Searchs for mail messages.
        """
        from djax.messaging.models import Message
        return Message.objects.search(self.model,query)
