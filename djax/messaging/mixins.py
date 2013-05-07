"""
Mixins for messaging functionality.
"""
from djax.messaging.models import Recipient, Message

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
    
    def inbox(self,unread_only=True):
        """
        Gets received messages for this recipient.
        """
        recipient = Recipient.objects.get_recipient(self)
        return recipient.inbox(unread_only=unread_only)
    
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
        

