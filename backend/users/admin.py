from django.contrib import admin
from .models import User, PassengerProfile

class CustomUserAdmin(admin.ModelAdmin):
    # What columns show up in the admin list view
    list_display = ('phone_number', 'is_verified', 'is_staff')
    # Adds a filter sidebar
    list_filter = ('is_verified', 'is_staff')
    # Adds a search bar that looks up phone numbers
    search_fields = ('phone_number',)
    ordering = ('phone_number',)

# Registering both models so they appear in the dashboard
admin.site.register(User, CustomUserAdmin)
admin.site.register(PassengerProfile)