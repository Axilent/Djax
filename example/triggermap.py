""" 
Example of trigger integration for Djax.
"""
from djax.triggers import trigger, affinity_trigger
from example.models import Article

triggers = (
    trigger(r'^$','pageview','home'),
    affnity_trigger(r'^article/(?P<article_id>\d+)/$','affinity','article',pk='article_id',model=Article),
    trigger(r'^topic/(?P<topic_slug>[\w-]+)/$','affinity','rtag',tag='$topic_slug'),
)