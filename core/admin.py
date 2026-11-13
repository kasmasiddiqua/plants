from django.contrib import admin
from .models import Observation, Plant


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'plant_type', 'user', 'planting_date')
    search_fields = ('name', 'plant_type', 'user__username')


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ('plant', 'captured_on', 'estimated_height_cm', 'leaf_count', 'growth_status')
    list_filter = ('growth_status', 'captured_on')
