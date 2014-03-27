Djax
====

Replacement for Django-Axilent.  Djax integrates Axilent with Django projects.


Model Field Conversions
---

The default behavior of a field map is to simply take the value from the incoming ACE content and assign that value to the recipient local model. This behavior can be overridden with the use of a *FieldConverter*.

A FieldConverter is an object that is placed as a value to the corresponding ACE content field key, within the field map. The FieldConverter is just an object (it does not require any particular parent class). Djax will look for two specific methods on the field converter object: `to_local_model` and `to_ace`, and the name of the local model field, defined as `field`.

Simple Example:

	class AuthorFieldConverter(object):
		"""Field converter changes string to related author (for article) and vice versa."""
		
		field = 'author'
		
		def to_local_model(self,ace_content,ace_field_value):
			"""String to related model."""
			return Author.objects.get(name=ace_field_value)
		
		def to_ace(self,local_model):
			"""Related model to string."""
			return local_model.author.name

In this case the field converter looks up a related model by name and returns the related model as the value to assign to the local model.

A field converter may be marked as **deferred**, in which case Djax will ensure that the local model is created *before* the conversion method is called, and will pass the local model into the conversion method as an argument.

With deferred converters, the return value for the `to_local_model` method is ignored.  It is up to the method to associate the value to the  local model.

Parent / Child Deferred Example:

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
		   
		  
