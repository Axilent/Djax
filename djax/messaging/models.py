"""
Models for Axilent messaging.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from pax.messaging import MessagingClient
from djax.gateway import cx

messaging_client = MessagingClient(cx)

class RecipientManager(models.Manager):
    """
    Manager class for Recipient.
    """
    def push_recipient(self,recipient_model):
        """
        Gets the recipient object for the specified model, and a flag indicating if the
        recipient was created.
        """
        from djax.messaging.mixins import AxilentRecipient
        if not isinstance(recipient_model,AxilentRecipient):
            raise ValueError('Model must extend AxilentRecipient')
        
        ctype = ContentType.objects.get_for_model(recipient_model)
        try:
            recipient = self.get(local_content_type=ctype,local_id=recipient_model.pk)
            content = {}
            for key,value in recipient_model.Axilent.field_map.items():
                content[value] = getattr(recipient_model,key)
            messaging_client.update_recipient(recipient.recipient_key,content)
            return recipient
        except Recipient.DoesNotExist:
            bus = recipient_model.Axilent.message_bus
            recipient_type = recipient_model.Axilent.recipient_type
            content = {}
            for key,value in recipient_model.Axilent.field_map.items():
                content[value] = getattr(recipient_model,key)
            
            recipient_key = messaging_client.create_recipient(bus,recipient_type,content)
            
            return self.create(local_content_type=ctype,
                               local_id=recipient_model.pk,
                               recipient_key=recipient_key)
    
    def get_recipient(self,recipient_model):
        """
        Gets the corresponding recipient for the model.
        """
        ctype = ContentType.objects.get_for_model(recipient_model)
        return self.get(local_content_type=ctype,local_id=recipient_model.pk)

class Recipient(models.Model):
    """
    A record of a recipient of a message.
    """
    local_content_type = models.ForeignKey(ContentType,related_name='axilent_message_recipients')
    local_id = models.IntegerField()
    recipient_key = models.CharField(max_length=100,unique=True)
    
    objects = RecipientManager()
    
    def inbox(self,unread_only=True):
        """
        Gets inbox messages for this recipient.
        """
        received_messages = messaging_client.inbox(self.recipient_key,unread_only=unread_only)
        message_keys = [message_dict['message_key'] for message_dict in received_messages]
        messages = Message.objects.filter(message_key__in=message_keys)
        for message in messages:
            ReceivedMessage.objects.get_or_create(message=message,recipient=self)
        
        return self.received_messages.all()
    
    def subscribe(self,topic):
        """
        Subscribes this recipient to a topic.
        """
        messaging_client.subscribe(self.recipient_key,topic)
    
    def unsubscribe(self,topic):
        """
        Unsubscribes this recipient from a topic.
        """
        messaging_client.unsubscribe(self.recipient_key,topic)
    
    def get_local(self):
        """
        Gets the local model corresponding to the recipient.
        """
        self.local_content_type.model_class().objects.get(pk=self.local_id)
    
    class Meta:
        unique_together = (('local_content_type','local_id'),)

class MessageManager(models.Manager):
    """
    Manager class for messages.
    """
    def create_message(self,message_model,sender):
        """
        Creates a message.  The sender is a Recipient object representing the sender
        of the message.
        """
        content = {}
        for key,value in message_model.Axilent.field_map.items():
            content[value] = getattr(message_model,key)
        
        message_key = messaging_client.create_message(message_model.Axilent.message_bus,
                                                      message_model.Axilent.message_type,
                                                      sender.recipient_key,
                                                      content)
        
        ctype = ContentType.objects.get_for_model(message_model)
        return self.create(local_content_type=ctype,
                           local_id=message_model.pk,
                           message_key=message_key,
                           sender_key=sender.recipient_key)
    
    def message_for_model(self,message_model):
        """
        Gets the message for the specified model.
        """
        ctype = ContentType.objects.get_for_model(message_model)
        return self.get(local_content_type=ctype,local_id=message_model.pk)

class Message(models.Model):
    """
    An axilent message - records the relationship between the local model and the remote message.
    """
    local_content_type = models.ForeignKey(ContentType,related_name='axilent_messages')
    local_id = models.IntegerField()
    message_key = models.CharField(max_length=100,unique=True) # the key for the message on Axilent
    sender_key = models.CharField(max_length=100)
    
    objects = MessageManager()
    
    def publish(self,topic):
        """
        Publishes this message on the specified topic.
        """
        messaging_client.publish_message(self.message_key,topic)
    
    def send(self,recipient):
        """
        Sends the message to the specified recipient.
        """
        messaging_client.send_message(self.message_key,recipient.recipient_key)
    
    def get_local(self):
        """
        Gets the local model for this message.
        """
        self.local_content_type.model_class().objects.get(pk=self.local_id)
    
    def update_received(self,recipient,read=True):
        """
        Updates the received version of this message, marking it read or unread
        for the specified recipient.
        """
        messaging_client.update_received_message(recipient.recipient_key,self.message_key,read=read)
    
    def delete_received(self,recipient):
        """
        Deletes the received version of this message for the recipient.
        """
        messaging_client.delete_received_message(recipient.recipient_key,self.message_key)
    
    def sender(self):
        """
        Gets the sender.
        """
        return Recipient.objects.get(recipient_key=self.sender_key)
    
    class Meta:
        unique_together = (('local_content_type','local_id'),)

class ReceivedMessage(models.Model):
    """
    A marker of a received message.
    """
    message = models.ForeignKey(Message,related_name='receipts')
    recipient = models.ForeignKey(Recipient,related_name='received_messages')
    unread = models.BooleanField(default=True)
    
    class Meta:
        unique_together = (('message','recipient'),)
