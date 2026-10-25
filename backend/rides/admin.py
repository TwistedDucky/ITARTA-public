from django.contrib import admin
from .models import Ride,FareConfig, DriverRequest

# Register your models here.
admin.site.register(Ride)
admin.site.register(FareConfig)
admin.site.register(DriverRequest)