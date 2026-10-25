from django.contrib import admin
from django.utils.html import format_html
from .models import DriverProfile

# --- 1. Custom Bulk Action ---
@admin.action(description='Verify and Approve selected drivers')
def approve_drivers(modeladmin, request, queryset):
    # This instantly flips is_approved to True for every checked box
    updated = queryset.update(is_approved=True)
    modeladmin.message_user(request, f'Successfully approved {updated} driver(s).')

# --- 2. The Verification Dashboard ---
@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    # What shows up on the main list page
    list_display = ('user', 'vehicle_number', 'license_number', 'is_approved', 'home_stand')
    list_filter = ('is_approved',)
    search_fields = ('user__phone_number', 'vehicle_number', 'license_number')
    
    # Register our custom button from above
    actions = [approve_drivers]

    # Tell Django to display our custom HTML image fields as read-only on the detail page
    readonly_fields = ('driver_photo_preview', 'license_photo_preview', 'vehicle_photo_preview')

    # Reorder the layout so the images sit beautifully at the bottom
    fieldsets = (
        ('Driver Information', {
            'fields': ('user', 'home_stand', 'is_approved')
        }),
        ('Vehicle & License Data', {
            'fields': ('vehicle_number', 'license_number', 'capacity')
        }),
        ('Verification Documents', {
            'fields': ('driver_photo_preview', 'license_photo_preview', 'vehicle_photo_preview')
        }),
    )

    # --- 3. HTML Image Rendering Logic ---
    def driver_photo_preview(self, obj):
        if obj.driver_photo:
            return format_html('<img src="{}" style="max-height: 200px; border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);" />', obj.driver_photo.url)
        return "No Photo Uploaded"
    driver_photo_preview.short_description = 'Driver Photo'

    def license_photo_preview(self, obj):
        if obj.license_photo:
            return format_html('<img src="{}" style="max-height: 200px; border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);" />', obj.license_photo.url)
        return "No License Uploaded"
    license_photo_preview.short_description = 'License Document'

    def vehicle_photo_preview(self, obj):
        if obj.vehicle_photo:
            return format_html('<img src="{}" style="max-height: 200px; border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);" />', obj.vehicle_photo.url)
        return "No Vehicle Photo"
    vehicle_photo_preview.short_description = 'Auto-Rickshaw Photo'