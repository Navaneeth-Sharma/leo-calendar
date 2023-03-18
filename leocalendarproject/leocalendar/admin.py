from django.contrib import admin
from .models import LeoEvent

class LeoEventAdmin(admin.ModelAdmin):
    pass

admin.site.register(LeoEvent, LeoEventAdmin)
