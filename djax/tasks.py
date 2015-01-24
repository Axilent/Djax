""" 
Celery tasks for Djax.
"""
from celery import task

@task
def trigger_async(trigger,profile,var_dict):
    """ 
    Async task to fire the trigger.
    """
    trigger._send_trigger(profile,var_dict)
