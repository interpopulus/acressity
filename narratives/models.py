from datetime import datetime
from experiences.models import Experience
from photologue.models import Gallery, Photo
from acressity.utils import embed_string

from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages


class Narrative(models.Model):
    '''
    Term describing description of an aspect of an experience.
    Think of these as pages or sections within a chapter;
    they are the sustenance of the experience.
    Examples of narratives include an update, thought, plan,
    itinerary, journal entry, publication, ad infinitum...
    '''
    narrative = models.TextField(help_text='The content of narrative. Where information regarding any thoughts, feelings, updates, etc can be added.', null=False)
    title = models.CharField(max_length=200, blank=True, null=True, help_text='Title of the narrative. If none given, defaults to date created.')
    experience = models.ForeignKey(Experience, related_name='narratives')
    author = models.ForeignKey(get_user_model(), related_name='narratives', null=False)
    date_created = models.DateTimeField(default=datetime.now, null=False, blank=True)
    date_modified = models.DateTimeField(auto_now=True, help_text='Updated every time object saved')
    category = models.CharField(max_length=50, null=True, blank=True, help_text='Optional information used to classify and order the narratives within the experience.')
    gallery = models.OneToOneField(Gallery, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(null=False, default=True, help_text='Public narratives will be displayed in the default views. Private ones are only seen by yourself and the other explorers in the narrative\'s experience. Changing the status of the narrative also changes the status of the photo gallery.')

    def __init__(self, *args, **kwargs):
        # Allows the quicker check of whether or not a particular field has changed
        # Considering using this in the method controlling status of is_public
        super(Narrative, self).__init__(*args, **kwargs)
        self.__original_is_public = self.is_public

    class Meta:
        #ordering = ['category']
        get_latest_by = 'date_created'

    def __unicode__(self):
        return self.title

    def model(self):
        return self.__class__.__name__

    def get_experience_author(self):
        return get_user_model().objects.get(pk=self.experience.author_id)

    def taste(self, chars=250):
        if len(self.narrative) > chars:
            return u'{0}...'.format(self.narrative[:chars])
        else:
            return self.narrative

    def is_author(self, request):
        if request.user.is_authenticated():
            if request.user.id == self.author_id:
                return True
            else:
                return False
        else:
            return False

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = datetime.now().strftime('%B %d, %Y')
        if self.__original_is_public != self.is_public:
            if self.gallery:
                self.gallery.is_public = self.is_public
                self.gallery.save()
        super(Narrative, self).save(*args, **kwargs)

    def get_next_narrative(self):
        try:
            narrative = self.get_next_by_date_created(experience_id=self.experience_id)
        except Narrative.DoesNotExist:
            narrative = None
        return narrative

    def get_previous_narrative(self):
        try:
            narrative = self.get_previous_by_date_created(experience_id=self.experience_id)
        except Narrative.DoesNotExist:
            narrative = None
        return narrative

    def embedded_narrative(self):
        return embed_string(self.narrative)
