from datetime import datetime

from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from experiences.models import Experience
from photologue.models import Photo
from explorers.models import Explorer


class ExperienceForm(ModelForm):
    experience = forms.CharField(widget=forms.TextInput(attrs={'class': 'larger'}))
    make_feature = forms.BooleanField(required=False,
                                      initial=False,
                                      help_text='Featuring an experience attaches the experience to the Dash for easy access and tells others that this is the experience you are actively pursuing.')
    date_created = forms.DateField(widget=SelectDateWidget(years=range(datetime.now().year, datetime.now().year-110, -1)), required=False)

    class Meta:
        model = Experience
        exclude = ('author', 'gallery', 'make_feature')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ExperienceForm, self).__init__(*args, **kwargs)

    def clean_date_created(self):
        date_created = self.cleaned_data.get('date_created')
        if not date_created:
            date_created = datetime.now()
        return date_created

    def clean_experience(self):
        experience = self.cleaned_data.get('experience')
        if len(experience) < 3:
            raise forms.ValidationError('Make the experience name a little more descriptive')
        return experience


class ExperienceBriefForm(ModelForm):
    class Meta:
        model = Experience
        fields = ('brief',)


class ExperiencePhotoForm(ModelForm):
    class Meta:
        model = Photo
        exclude = ('title_slug',)
