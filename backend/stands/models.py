from django.contrib.gis.db import models
from django.conf import settings

class State(models.Model):
    """Permanent list of States for admin dropdowns."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2,unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    """Permanent list of Districts, linked to a specific State."""
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True)

    class Meta:
        unique_together = ('state', 'name') 

    def __str__(self):
        return f"{self.name} ({self.state.name})"

class Stand(models.Model):
    """Represents a physical auto-rickshaw stand."""
    stand_code = models.CharField(max_length=8, unique=True,blank=True)
    name = models.CharField(max_length=150)
    
    # Links to the District model to ensure clean, searchable data
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name='stands')
    place = models.CharField(max_length=100, help_text="Specific locality or junction")
    
    # PostGIS Spatial Fields
    location = models.PointField(srid=4326, geography=True, help_text="Exact center GPS point",spatial_index=True)
    area = models.PolygonField(srid=4326, help_text="Geofence boundary of the parking area",spatial_index=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    """Overrided save method to automatically add the stand code. The stand code is only sequentially added so there is no race conditions.
    Here the stand code is becomes like KLKN0001 where first two characters represent the state and the next the district"""

    def save(self, **kwargs):
        if not self.stand_code:
            num = Stand.objects.filter(district=self.district).count() + 1
            number = f"{num:04}"
            self.stand_code = self.district.state.code + self.district.code  + number
        super().save(**kwargs)

    def __str__(self):
        return f"{self.stand_code} - {self.name} ({self.district.name})"
