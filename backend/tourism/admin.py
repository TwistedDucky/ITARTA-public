from django.contrib import admin
from django.contrib.gis.db import models
from django.contrib.gis.forms import OSMWidget
from django_json_widget.widgets import JSONEditorWidget
from django.contrib.gis.geos import Point
from django import forms
from .models import Place, PlaceImage, Rating


class PlaceAdminForm(forms.ModelForm):
    latitude = forms.FloatField(
        help_text="e.g. 10.8505",
        required=True
    )
    longitude = forms.FloatField(
        help_text="e.g. 76.2711",
        required=True
    )

    class Meta:
        model = Place
        exclude = ['location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.location:
            self.fields['latitude'].initial = self.instance.location.y
            self.fields['longitude'].initial = self.instance.location.x

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get('latitude')
        lng = self.cleaned_data.get('longitude')
        if lat and lng:
            instance.location = Point(lng, lat, srid=4326)
        if commit:
            instance.save()
        return instance


class PlaceImageInline(admin.TabularInline):
    model = PlaceImage
    extra = 3


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    form = PlaceAdminForm
    inlines = [PlaceImageInline]
    list_display = ['name', 'category', 'address', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'address']
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }


@admin.register(PlaceImage)
class PlaceImageAdmin(admin.ModelAdmin):
    list_display = ['place', 'order']


@admin.register(Rating)

class RatingAdmin(admin.ModelAdmin):
    list_display = ['user','place','rating','review','created_at']