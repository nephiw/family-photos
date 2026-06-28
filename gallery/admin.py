from django.contrib import admin
from django.utils.html import format_html
from .models import Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_by', 'uploaded_at', 'thumbnail_preview')
    list_filter = ('uploaded_by', 'uploaded_at')
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" style="border-radius:4px; border: 2px solid #00f0ff;" />', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Thumbnail Preview'

