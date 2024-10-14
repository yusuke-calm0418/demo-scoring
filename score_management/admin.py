from django.contrib import admin
from .models import ScoreSetting, Link

admin.site.register(ScoreSetting)

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('url',)
    search_fields = ('url',)
