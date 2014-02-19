from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.hashers import make_password

from photologue.models import Photo, Gallery
from acressity.utils import embed_string

# @receiver(m2m_changed, sender=Narrative)
# def experience_handler(sender, **kwargs):
# 	pass


class ExperienceManager(models.Manager):
    def get_random(self, num=1):
        return self.order_by('?')[:num]


class Experience(models.Model):
    '''
    The term signifying a single venture, goal, wish, exploration,
    (ad infinitum) that an explorer has expressed as being willing
    of attaining. Think of these as the titles of chapters within
    a book about your journey.
    '''

    experience = models.CharField(max_length=200, help_text='Title of the experience.')  # Add null=False
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='authored_experiences', help_text='Explorer who created the experience. Has the ability of sending requests to other explorers to become comrades in this experience.')
    date_created = models.DateTimeField(default=datetime.now, null=False, blank=True)
    date_modified = models.DateTimeField(auto_now=True, help_text='Updated every time object saved', null=True, blank=True)
    brief = models.TextField(blank=True, null=True, help_text='Written description of the experience to provide a little insight.')
    status = models.CharField(max_length=160, null=True, blank=True, help_text='Optional short state of the experience at the moment.')
    gallery = models.OneToOneField(Gallery, null=True, blank=True, on_delete=models.SET_NULL)
    is_public = models.BooleanField(default=True, help_text='Changing public and private status is only available to the experience\'s author. Private experiences are only seen by its explorers and those providing a correct password if one is selected. A correct password also provides access to all private narratives. Making an experience private will also set all of it\'s narratives to being private. Changing the status of the experience changes the status of the experience\'s gallery. However, private narratives do not become public when the experience is changed from private to public.')
    password = models.CharField(_('password'), max_length=128, null=True, blank=True, help_text='Submitting the correct password provides access to the experience if it is private as well as all of the private narratives.')
    search_term = models.CharField(max_length=80, null=True, blank=True, unique=True, help_text='Short phrase or word identifying the experience, allows access by typing http://acressity.com/your_search_term_here. Needs to be unique and cannot be the same as another explorer\'s trailname')

    objects = ExperienceManager()

    def __init__(self, *args, **kwargs):
        # Allows the quicker check of whether or not a particular field has changed
        # Considering using this in the method controlling status of is_public
        super(Experience, self).__init__(*args, **kwargs)
        self.__original_is_public = self.is_public

    def __unicode__(self):
        return self.experience

    def __str__(self):
        return self.__unicode__()

    def model(self):
        return self.__class__.__name__

    def get_photos(self):
        queryset = self.gallery.photos.none()
        if self.gallery:
            queryset = queryset | self.gallery.photos.all()
        narrative_galleries = [narrative.gallery for narrative in self.narratives.all() if narrative.gallery]
        for gallery in narrative_galleries:
            queryset = queryset | gallery.photos.all()
        return queryset

    def is_author(self, request):
        if request.user.is_authenticated():
            if request.user == self.author:
                return True
            else:
                return False
        else:
            return False

    def is_comrade(self, request):
        if request.user.is_authenticated():
            if request.user in self.explorers.all():
                return True
        return False

    def ordered_narratives(self):
        return self.narratives.order_by('-date_created')

    def comrades(self, request):
        return self.explorers.exclude(id=request.user.id)

    def create_gallery(self):
        gallery = Gallery(title=self.experience, content_type=ContentType.objects.get(model='experience'), object_pk=self.id, is_public=self.is_public)
        gallery.save()
        return gallery

    def get_galleries(self):
        object_list = []
        for narrative in self.narratives.all():
            if narrative.gallery:
                object_list.append(narrative.gallery)
        if self.gallery:
            object_list.append(self.gallery)
        return object_list

    def latest_narrative(self):
        if self.narratives.exists() and self.narratives.filter(is_public=True):
            return self.public_narratives().latest('date_created')

    def public_narratives(self):
        'Return an ordered queryset of all the public narratives in this experience'
        return self.ordered_narratives().filter(is_public=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def save(self, *args, **kwargs):
        # Feature for toggling the experience gallery being public
        # with the toggling of experience is_public
        if self.__original_is_public != self.is_public:
            if not self.is_public:
                for narrative in self.narratives.filter(is_public=True):
                    narrative.is_public = False
                    narrative.save()
            if self.gallery:
                self.gallery.is_public = self.is_public
                self.gallery.save()
        super(Experience, self).save(*args, **kwargs)

    def embedded_brief(self):
        return embed_string(self.brief)


class FeaturedExperience(models.Model):
    experience = models.ForeignKey(Experience)
    date_featured = models.DateTimeField(default=datetime.now)

    objects = ExperienceManager()

    def __unicode__(self):
        return self.experience.experience
