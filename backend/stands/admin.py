from django.contrib.gis import admin
from .models import State, District, Stand

admin.site.register(State)
admin.site.register(District)

# 2. MERGED: Interactive Map + Driver Queue Table!
@admin.register(Stand)
class StandAdmin(admin.GISModelAdmin):
    """Provides an interactive map interface for creating stands AND shows the active queue."""
    list_display = ('stand_code', 'name', 'district', 'is_active')
    list_filter = ('district__state', 'is_active')
    
    # Modern Django configuration for map widgets
    gis_widget_kwargs = {
        'attrs': {
            'default_lon': 76.2711,
            'default_lat': 10.8505,
            'default_zoom': 7, 
        }
    }
