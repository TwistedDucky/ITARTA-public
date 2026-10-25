import uuid
from django.contrib.gis.db import models
from core.storage_backends import PublicMediaStorage
from django.core.validators import MinValueValidator,MaxValueValidator
from users.models import PassengerProfile


def thumbnail_upload_path(instance, filename):
    return f'tourism/thumbnails/{instance.uuid}/{filename}'


def place_image_upload_path(instance, filename):
    return f'tourism/images/{instance.place.uuid}/{filename}'


class Place(models.Model):

    CATEGORY_CHOICES = [
        ('RESTAURANT', 'Restaurant'),
        ('CAFE', 'Cafe'),
        ('RESORT', 'Resort'),
        ('HOTEL', 'Hotel'),
        ('HOMESTAY', 'Homestay'),
        ('TOURIST_SPOT', 'Tourist Spot')
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    address = models.CharField(max_length=300)
    location = models.PointField(srid=4326, geography=True, help_text="Enter as POINT(longitude latitude)", spatial_index=True)
    contact_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    thumbnail = models.ImageField(storage=PublicMediaStorage(), upload_to=thumbnail_upload_path)
    metadata = models.JSONField(default=dict)
    average_rating = models.DecimalField(max_digits=2,decimal_places=1,default=0.0)
    total_ratings = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class PlaceImage(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(storage=PublicMediaStorage(), upload_to=place_image_upload_path)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.place.name} - image {self.order}"

class Rating(models.Model):
    user = models.ForeignKey(PassengerProfile,
                             on_delete=models.PROTECT,
                             related_name="ratings")
    place = models.ForeignKey(Place,
                              on_delete=models.CASCADE,
                              related_name="ratings")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user","place"]]

    def save(self, *args, **kwargs):
        place = self.place
        
        if self.pk:  # this is an UPDATE
            old_rating = Rating.objects.get(pk=self.pk)
            new_average_rating = ((place.average_rating * place.total_ratings) -old_rating.rating + self.rating)/place.total_ratings
            place.average_rating = round(new_average_rating,1)
            
        else:  # this is a CREATE
            new_average_rating = ((place.average_rating*place.total_ratings) + self.rating)/(place.total_ratings+1)
            place.average_rating = round(new_average_rating,1)
            place.total_ratings += 1
        
        place.save()
        super().save(*args, **kwargs)
        

