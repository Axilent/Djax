Djax
====

**Django / ACE Integration**

Djax integrates the Django web framework with `Axilent
ACE <http://www.axilent.com/products/ace/>`__. ACE is a sophisticated
content targeting system that can be used for product recommendations,
related content, personalization and contextual advertising.

Djax links Django models with ACE content types, enabling the use of ACE
as a CMS for a Django website. It also provides easy integration with
ACE's targeting Content Channels, and provides integration with ACE's
user profiling system.

Installation
~~~~~~~~~~~~

To install Djax with Pip:

::

    pip install Djax

Then, add ``djax`` to your ``INSTALLED_APPS``.

Finally, you will need to ``syncdb`` to generate Djax's tables.

Integrating ACE Published Content With Django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to use content that is authored our sourced in ACE in a Django
website, integrate the desired Django model with Djax using the
ACEContent mixin.

::

    # your-app/models.py

    from django.db import models
    from djax.content import ACEContent

    class Article(models.Model,ACEContent):
         title = models.CharField(max_length=100)
         body = models.TextField()
         
         class ACE:
             content_type = 'Article'
             field_map = {
                 'title':'title',
                 'body':'body',
             }

Several important things are happening here:

1. In addition to inheriting from ``models.Model`` like an ordinary
   Django model, the Article class also inherits from ``ACEContent``.
   This will allow Djax to identify it as a local type of content that
   should be bound to an ACE Content Type.
2. In the ``ACE`` inner class, the ``content_type`` attribute identifies
   the ACE Content Type with which this model should be associated.
3. In the ``ACE inner class`` the ``field_map`` dictionary defines the
   mappings between the ACE Content Type fields (the keys in the
   dictionary) and the local model's fields (the values in the
   dictionary).

When Djax syncs with ACE, it will create or update this model with the
mapped content from ACE.

Managing Foreign Key Relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ACE is not a relational database, and accordingly does not hold content
to the same level of integral rigor as an RDBMS. However, it does
provide some means to directly link one content item to another using a
field type called a **Content Link**.

Djax provides a way to convert an ACE Content Link into a Django foreign
key relationship. Let's say you have a local model that has an Author
model and an Article model. The Article model has a foriegn key field
that points to the Author model. In ACE, the Article Content Type would
have a Content Link field that would be used to point at an author.

The integration can be implemented without any special work using Djax:

::

    class Author(models.Model,ACEContent):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)
        
        class ACE:
            content_type = 'Author'
            field_map = {
                'first_name':'first_name',
                'last_name':'last_name',
            }
      
      class Article(models.Model,ACEContent):
          author = models.ForeignKey(model=Author,related_name='articles')
          title = models.CharField(max_length=100)
          body = models.TextField()
         
          class ACE:
             content_type = 'Article'
             field_map = {
                 'author','author',
                 'title':'title',
                 'body':'body',
             }

During a sync, incoming Content Link data from ACE will be enough to
alert Djax to look for a local model-to-ACE Content Type mapping, and
create a foreign key association in the local models.

Because the local model Article does not allow Article objects to exist
in the database without an associated Author, it is important to ensure
that the Author object is sync'd to the local database first. In a bulk
sync this will be taken care of automatically, but when syncing once
content item at a time, an error will occur if the Article object is
sync'd before the associated Author object.

Nullable Foreign Key Relations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What if a foreign key relationship is nullable? In the example given
above, what if not all Articles have Authors? It's not a problem in ACE,
just leave the appropriate Content Link field empty. But an additional
step is required with Djax integration:

::

      class Article(models.Model,ACEContent):
          author = models.ForeignKey(model=Author,null=True,related_name='articles')
          title = models.CharField(max_length=100)
          body = models.TextField()
         
          class ACE:
             content_type = 'Article'
             field_map = {
                 'author',NullableForeignKeyConverter('author'),
                 'title':'title',
                 'body':'body',
             }

There are two changes in the Article model. First the author field has
been marked ``null=True`` to indicate to Django that the Article model
may not have an Author.

Secondly, the simple string ('author') indicating that the author field
in the incoming content from ACE should be mapped to the local author
field has been replaced by a ``NullableForeignKeyConverter`` object.
This is an indication to Djax that it should apply a special process to
the incoming data: either find a local model that corresponds to the
supplied Content Link data, or leave the field null.

Managing Many-to-Many Relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ACE can also handle many-to-many relations using the Content Link List
field type. Let's say we have a local model that defines a many-to-many
relation between Publication and Author objects. In ACE, the Author
object would have a publication field that was a Content Link List that
would be used to associate it with Publications.

To implement the integration in Djax we would do this:

::

    class Publication(models.Model,ACEContent):
        name = models.CharField(max_length=100)
        
        class ACE:
            content_type = 'Publication'
            field_map = {
                'name':'name',
            }

    class Author(models.Model,ACEContent):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)
        publications = models.ManyToManyField(Publication,related_name='authors')
        
        class ACE:
            content_type = 'Author'
            field_map = {
                'first_name':'first_name',
                'last_name':'last_name',
                'publications':M2MFieldConverter('publications'),
            }

In the Author model's ``ACE`` inner class, we have specified the
``M2MFieldConverter`` for the publications field. This lets Djax know to
convert incoming Content Link List data into a local many-to-many
relation.

Implementing Your Own Field Converters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default behavior of a field map is to simply take the value from the
incoming ACE content and assign that value to the recipient local model.
This behavior can be overridden with the use of a *FieldConverter*.

A FieldConverter is an object that is placed as a value to the
corresponding ACE content field key, within the field map. The
FieldConverter is just an object (it does not require any particular
parent class). Djax will look for two specific methods on the field
converter object: ``to_local_model`` and ``to_ace``, and the name of the
local model field, defined as ``field``.

Simple Example:

::

    class AuthorFieldConverter(object):
        """Field converter changes string to related author (for article) and vice versa."""
        
        field = 'author'
        
        def to_local_model(self,ace_content,ace_field_value):
            """String to related model."""
            return Author.objects.get(name=ace_field_value)
        
        def to_ace(self,local_model):
            """Related model to string."""
            return local_model.author.name

In this case the field converter looks up a related model by name and
returns the related model as the value to assign to the local model.

A field converter may be marked as **deferred**, in which case Djax will
ensure that the local model is created *before* the conversion method is
called, and will pass the local model into the conversion method as an
argument.

With deferred converters, the return value for the ``to_local_model``
method is ignored. It is up to the method to associate the value to the
local model.

Parent / Child Deferred Example:

::

    class MusicLabelCatalogConverter(object):
        """Converts the bands signed to the parent label."""
        
        field = 'bands'
        deferred = True
        
        def to_local_model(self,ace_content,ace_field_value,local_model):
            """Gets or creates associated local band objects. Ace provides a list of band names."""
            for band_name in ace_field_value:
                Band.objects.get_or_create(label=local_model,name=band_name)
            
            # clean up unassociated bands
            [band.delete() for band in local_model.bands.exclude(name__in=ace_field_value)]
        
        def to_ace(self,local_model):
            """Returns a list of band names for ace."""
            return [band.name for band in local_model.bands.all()]

ACEContent Methods
~~~~~~~~~~~~~~~~~~

A Django model that also inherits from ACEContent will have several
additional methods that allow it to be programmatically managed from a
Django app, if desired.

ACEContent.get\_axilent\_content\_key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns the local model's ACE content key. If the content does not exist
within the ACE account, it will return None. The content key is a GUID
rendered in hex format.

ACEContent.get\_axilent\_content\_type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns the name of the ACE Content Type for the model.

ACEContent.sync\_with\_axilent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forces the local model to update from content from ACE. If there is no
corresponding content item in the ACE account, this method will do
nothing.

ACEContent.to\_content\_dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns content values as a dictionary according to the ``field_map``.

ACEContent.push\_to\_library
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pushes the local values of the content into the associated ACE library.
This method returns a 2-tuple of booleans, indicating 1. if the library
was updated and 2. if a new content item was created in the library.

ACEContent.push\_to\_graphstack
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Puhes the local values of the content directly into the associated
GraphStack. A GraphStack in ACE is a logical container for deployed or
published content.

ACEContent.archive
^^^^^^^^^^^^^^^^^^

Removes the content from any GraphStack where it has been deployed.

ACEContent.live\_delete
^^^^^^^^^^^^^^^^^^^^^^^

Removes the associated ACE content item from the active GraphStack where
it is deployed.

ACEContent.tag
^^^^^^^^^^^^^^

Tags the content item within the associated ACE library.

ACEContent.detag
^^^^^^^^^^^^^^^^

De-tags the content item within the associated ACE library.

ACEContent.live\_tag
^^^^^^^^^^^^^^^^^^^^

Tags the content item where it has been deployed in the associated
GraphStack.

ACEContent.live\_detag
^^^^^^^^^^^^^^^^^^^^^^

De-tags the content item where it has been deployed in the associated
GraphStack.

ACEContent.reindex\_search
^^^^^^^^^^^^^^^^^^^^^^^^^^

Forces search re-indexing of the deployed associated content.

ACEContent.trigger\_affinity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sends an affinity trigger for this content to ACE.

ACEContent.trigger\_ban
^^^^^^^^^^^^^^^^^^^^^^^

Sends a ban trigger for this content to ACE.

Setting Up Djax and ACE to Handle User-Generated Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A common scenario is User Generated Content (UGC), in which user's of
the website create content, in the form of Django models, which then
needs to be pushed back into the ACE library for administrative review.
Djax and ACE now support this round-trip model for content.

In the ACE project, first create a new **Content Source** for the
Content Type that you want to round-trip. Content Sources are found in
the settings panel, for each content type under the Content Types
section of the ACE project.

The new Content Source should be of the type **Djax User Generated
Content**. When creating the Content Source, you will need to set the
refresh interval, the URL pointing to the Djax install, and an auth
token.

In your code, you set up your model as ``ACEContent`` as usual, defining
the ACE content type and the field map in the ``ACE`` subclass.

Everytime the Content Source passes the refresh interval, it will query
your Djax install. At this point the Djax install will push the content
into the ACE library, either creating new content items or updating
existing ones.
